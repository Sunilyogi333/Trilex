from django.db import transaction
from django.shortcuts import get_object_or_404

from bookings.models import Booking
from chat.models import ChatRoom, ChatParticipant
from base.constants.user_roles import UserRoles


class RoomService:

    @staticmethod
    def validate_booking_access(user, booking: Booking):
        """
        Ensure user is part of booking.
        """
        if user != booking.created_by and user != booking.created_to:
            raise PermissionError("You are not allowed to access this booking.")

    @staticmethod
    @transaction.atomic
    def create_or_get_room(user, booking_id):
        """
        Create chat room if not exists.
        """

        booking = get_object_or_404(Booking, id=booking_id)

        # Validate booking access
        RoomService.validate_booking_access(user, booking)

        # Room already exists
        if hasattr(booking, "chat_room"):
            return booking.chat_room

        # Create new room
        room = ChatRoom.objects.create(booking=booking)

        # Always add client
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
            # Firm admin is firm.user
            ChatParticipant.objects.create(
                room=room,
                user=booking.created_to,
                is_admin=True
            )

        return room
