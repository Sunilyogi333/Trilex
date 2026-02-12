from rest_framework import serializers
from django.contrib.auth import get_user_model

from chat.models import ChatRoom, ChatMessage, ChatParticipant
from accounts.api.serializers import UserSerializer
from bookings.models import Booking
from base.pagination import DefaultPageNumberPagination
from chat.services.message_service import MessageService

User = get_user_model()


# ---------------------------------
# PARTICIPANT
# ---------------------------------

class ChatParticipantSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = ChatParticipant
        fields = (
            "id",
            "user",
            "is_admin",
            "joined_at",
        )


# ---------------------------------
# ROOM LIST SERIALIZER
# ---------------------------------

class ChatRoomListSerializer(serializers.ModelSerializer):
    booking_id = serializers.UUIDField(source="booking.id")
    participants = ChatParticipantSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = (
            "id",
            "booking_id",
            "participants",
            "last_message",
            "unread_count",
            "updated_at",
        )

    def get_last_message(self, obj):
        last = obj.messages.order_by("-created_at").first()
        if not last:
            return None
        return {
            "id": last.id,
            "sender": last.sender.email,
            "message": last.message,
            "created_at": last.created_at,
        }

    def get_unread_count(self, obj):
        user = self.context["request"].user
        return MessageService.get_unread_count(obj, user)


# ---------------------------------
# MESSAGE SERIALIZER
# ---------------------------------

class ChatMessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)

    class Meta:
        model = ChatMessage
        fields = (
            "id",
            "sender",
            "message",
            "created_at",
        )


# ---------------------------------
# ADD/REMOVE LAWYER
# ---------------------------------

class ModifyParticipantSerializer(serializers.Serializer):
    lawyer_user_id = serializers.UUIDField(required=True)
