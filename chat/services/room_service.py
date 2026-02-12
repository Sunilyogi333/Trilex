from django.db import transaction
from django.shortcuts import get_object_or_404

from bookings.models import Booking
from chat.models import ChatRoom, ChatParticipant
from base.constants.user_roles import UserRoles
from base.constants.booking_status import BookingStatus


class RoomService:

    @staticmethod
    def validate_booking_access(user, booking: Booking):
        if user != booking.created_by and user != booking.created_to:
            raise PermissionError("You are not allowed to access this booking.")

    @staticmethod
    @transaction.atomic
    def create_or_get_room(user, booking_id):
        booking = get_object_or_404(Booking, id=booking_id)

        # ✅ Ensure booking is accepted
        if booking.status != BookingStatus.ACCEPTED:
            raise PermissionError("Chat is available only for accepted bookings.")

        RoomService.validate_booking_access(user, booking)

        # ✅ Proper room existence check
        try:
            return booking.chat_room
        except ChatRoom.DoesNotExist:
            pass

        room = ChatRoom.objects.create(booking=booking)

        # Add client
        ChatParticipant.objects.create(
            room=room,
            user=booking.created_by,
            is_admin=False
        )

        # If booking to lawyer
        if booking.created_to.role == UserRoles.LAWYER:
            ChatParticipant.objects.create(
                room=room,
                user=booking.created_to,
                is_admin=False
            )

        # If booking to firm
        elif booking.created_to.role == UserRoles.FIRM:
            ChatParticipant.objects.create(
                room=room,
                user=booking.created_to,
                is_admin=True
            )

        return room
