from django.db import transaction
from django.core.exceptions import PermissionDenied, ValidationError

from bookings.models import Booking
from base.constants.booking_status import BookingStatus
from base.constants.user_roles import UserRoles
from base.constants.verification import VerificationStatus


class BookingService:

    # -------------------------
    # INTERNAL HELPERS
    # -------------------------
    @staticmethod
    def ensure_verified(user):
        """
        Ensure user has VERIFIED identity based on role.
        Acts as a safety net even if permissions fail.
        """
        if user.role == UserRoles.CLIENT:
            verification = getattr(user, "client_verification", None)
        elif user.role == UserRoles.LAWYER:
            verification = getattr(user, "bar_verification", None)
        elif user.role == UserRoles.FIRM:
            verification = getattr(user, "firm_verification", None)
        else:
            verification = None

        if not verification or verification.status != VerificationStatus.VERIFIED:
            raise ValidationError("User must be verified.")

    # -------------------------
    # CREATE BOOKING
    # -------------------------
    @staticmethod
    @transaction.atomic
    def create_booking(*, created_by, created_to, **data):
        # role checks
        if created_by.role != UserRoles.CLIENT:
            raise PermissionDenied("Only clients can create bookings.")

        if created_to.role not in [UserRoles.LAWYER, UserRoles.FIRM]:
            raise ValidationError(
                "Booking can only be sent to a lawyer or firm."
            )

        if created_by == created_to:
            raise ValidationError("Cannot create booking for yourself.")

        # verification checks (defense-in-depth)
        BookingService.ensure_verified(created_by)
        BookingService.ensure_verified(created_to)

        # duplicate pending booking check
        if Booking.objects.filter(
            created_by=created_by,
            created_to=created_to,
            status=BookingStatus.PENDING,
        ).exists():
            raise ValidationError(
                "You already have a pending booking with this user."
            )

        booking = Booking.objects.create(
            created_by=created_by,
            created_to=created_to,
            **data,
        )

        return booking

    # -------------------------
    # ACCEPT BOOKING
    # -------------------------
    @staticmethod
    @transaction.atomic
    def accept_booking(*, booking, user):
        if booking.created_to != user:
            raise PermissionDenied("You cannot accept this booking.")

        if booking.status != BookingStatus.PENDING:
            raise ValidationError(
                "Only pending bookings can be accepted."
            )

        BookingService.ensure_verified(user)

        booking.status = BookingStatus.ACCEPTED
        booking.save(update_fields=["status", "updated_at"])

        return booking

    # -------------------------
    # REJECT BOOKING
    # -------------------------
    @staticmethod
    @transaction.atomic
    def reject_booking(*, booking, user):
        if booking.created_to != user:
            raise PermissionDenied("You cannot reject this booking.")

        if booking.status != BookingStatus.PENDING:
            raise ValidationError(
                "Only pending bookings can be rejected."
            )

        BookingService.ensure_verified(user)

        booking.status = BookingStatus.REJECTED
        booking.save(update_fields=["status", "updated_at"])

        return booking
