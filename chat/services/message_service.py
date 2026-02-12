from django.db import transaction
from django.db.models import OuterRef, Exists
from django.shortcuts import get_object_or_404

from chat.models import ChatRoom, ChatMessage, ChatParticipant, MessageRead


class MessageService:

    @staticmethod
    def validate_room_access(user, room: ChatRoom):
        """
        Ensure user is participant in room.
        """
        if not ChatParticipant.objects.filter(room=room, user=user).exists():
            raise PermissionError("You are not a participant in this room.")

    @staticmethod
    @transaction.atomic
    def create_message(room_id, sender, message_text):
        room = get_object_or_404(ChatRoom, id=room_id)

        MessageService.validate_room_access(sender, room)

        message = ChatMessage.objects.create(
            room=room,
            sender=sender,
            message=message_text
        )

        return message

    @staticmethod
    @transaction.atomic
    def mark_room_as_read(room_id, user):
        room = get_object_or_404(ChatRoom, id=room_id)

        MessageService.validate_room_access(user, room)

        messages = ChatMessage.objects.filter(
            room=room
        ).exclude(sender=user)

        existing_reads = MessageRead.objects.filter(
            message=OuterRef("pk"),
            user=user
        )

        unread_messages = messages.annotate(
            is_read=Exists(existing_reads)
        ).filter(is_read=False)

        MessageRead.objects.bulk_create([
            MessageRead(message=msg, user=user)
            for msg in unread_messages
        ])

    @staticmethod
    def get_unread_count(room, user):
        messages = ChatMessage.objects.filter(
            room=room
        ).exclude(sender=user)

        existing_reads = MessageRead.objects.filter(
            message=OuterRef("pk"),
            user=user
        )

        unread = messages.annotate(
            is_read=Exists(existing_reads)
        ).filter(is_read=False)

        return unread.count()
