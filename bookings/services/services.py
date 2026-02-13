from django.db import transaction
from rest_framework.exceptions import (
    APIException,
    PermissionDenied,
)

from bookings.models import Booking
from base.constants.booking_status import BookingStatus
from base.constants.user_roles import UserRoles
from base.constants.verification import VerificationStatus

from notifications.services import NotificationService
from notifications.constants import NotificationType


class BookingService:

    # INTERNAL
    @staticmethod
    def ensure_verified(user):
        if user.role == UserRoles.CLIENT:
            verification = getattr(user, "client_verification", None)
        elif user.role == UserRoles.LAWYER:
            verification = getattr(user, "bar_verification", None)
        elif user.role == UserRoles.FIRM:
            verification = getattr(user, "firm_verification", None)
        else:
            verification = None

        if not verification or verification.status != VerificationStatus.VERIFIED:
            raise APIException("User must be verified.")

    # CREATE
    @staticmethod
    @transaction.atomic
    def create_booking(*, created_by, created_to, **data):

        if created_by.role != UserRoles.CLIENT:
            raise PermissionDenied("Only clients can create bookings.")

        if created_to.role not in (UserRoles.LAWYER, UserRoles.FIRM):
            raise APIException("Booking can only be sent to a lawyer or firm.")

        if created_by == created_to:
            raise APIException("Cannot create booking for yourself.")

        BookingService.ensure_verified(created_by)
        BookingService.ensure_verified(created_to)

        if Booking.objects.filter(
            created_by=created_by,
            created_to=created_to,
            status=BookingStatus.PENDING,
        ).exists():
            raise APIException(
                "You already have a pending booking with this user."
            )

        booking = Booking.objects.create(
            created_by=created_by,
            created_to=created_to,
            **data,
        )

        # Send notification AFTER commit
        transaction.on_commit(lambda: NotificationService.create_notification(
            recipient=created_to,
            notification_type=NotificationType.BOOKING_CREATED,
            title="New Booking Request",
            message=f"You have received a new booking request.",
            entity_type="booking",
            entity_id=booking.id,
            content_object=booking,
            metadata={
                "booking_id": str(booking.id),
            },
            actor=created_by,
        ))

        return booking

    # ACCEPT
    @staticmethod
    @transaction.atomic
    def accept_booking(*, booking, user):

        if booking.created_to != user:
            raise PermissionDenied("You cannot accept this booking.")

        if booking.status != BookingStatus.PENDING:
            raise APIException("Only pending bookings can be accepted.")

        BookingService.ensure_verified(user)

        booking.status = BookingStatus.ACCEPTED
        booking.save(update_fields=["status", "updated_at"])

        # Notify client
        transaction.on_commit(lambda: NotificationService.create_notification(
            recipient=booking.created_by,
            notification_type=NotificationType.BOOKING_ACCEPTED,
            title="Booking Accepted",
            message="Your booking request has been accepted.",
            entity_type="booking",
            entity_id=booking.id,
            content_object=booking,
            metadata={
                "booking_id": str(booking.id),
            },
            actor=user,
        ))

        return booking

    # REJECT
    @staticmethod
    @transaction.atomic
    def reject_booking(*, booking, user):

        if booking.created_to != user:
            raise PermissionDenied("You cannot reject this booking.")

        if booking.status != BookingStatus.PENDING:
            raise APIException("Only pending bookings can be rejected.")

        BookingService.ensure_verified(user)

        booking.status = BookingStatus.REJECTED
        booking.save(update_fields=["status", "updated_at"])

        # Notify client
        transaction.on_commit(lambda: NotificationService.create_notification(
            recipient=booking.created_by,
            notification_type=NotificationType.BOOKING_REJECTED,
            title="Booking Rejected",
            message="Your booking request has been rejected.",
            entity_type="booking",
            entity_id=booking.id,
            content_object=booking,
            metadata={
                "booking_id": str(booking.id),
            },
            actor=user,
        ))

        return booking
