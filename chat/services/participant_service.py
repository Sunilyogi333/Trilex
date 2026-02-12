from django.shortcuts import get_object_or_404
from django.db import transaction

from chat.models import ChatRoom, ChatParticipant
from lawyers.models import Lawyer
from base.constants.user_roles import UserRoles


class ParticipantService:

    @staticmethod
    def _validate_firm_admin(user, room: ChatRoom):
        """
        Ensure user is firm admin in this room.
        """
        participant = ChatParticipant.objects.filter(
            room=room,
            user=user,
            is_admin=True
        ).first()

        if not participant:
            raise PermissionError("Only firm admin can manage participants.")

        if room.booking.created_to.role != UserRoles.FIRM:
            raise PermissionError("This is not a firm booking room.")

    @staticmethod
    @transaction.atomic
    def add_lawyer(room_id, request_user, lawyer_user_id):
        room = get_object_or_404(ChatRoom, id=room_id)

        ParticipantService._validate_firm_admin(request_user, room)

        lawyer = get_object_or_404(Lawyer, user__id=lawyer_user_id)

        # Ensure lawyer belongs to this firm
        if lawyer.user.firm_profile != room.booking.created_to.firm_profile:
            raise PermissionError("Lawyer does not belong to this firm.")

        # Prevent duplicate
        if ChatParticipant.objects.filter(room=room, user=lawyer.user).exists():
            return

        ChatParticipant.objects.create(
            room=room,
            user=lawyer.user,
            is_admin=False
        )

    @staticmethod
    @transaction.atomic
    def remove_lawyer(room_id, request_user, lawyer_user_id):
        room = get_object_or_404(ChatRoom, id=room_id)

        ParticipantService._validate_firm_admin(request_user, room)

        participant = get_object_or_404(
            ChatParticipant,
            room=room,
            user__id=lawyer_user_id
        )

        # Cannot remove client
        if participant.user == room.booking.created_by:
            raise PermissionError("Cannot remove client.")

        # Cannot remove firm admin
        if participant.is_admin:
            raise PermissionError("Cannot remove firm admin.")

        participant.delete()
