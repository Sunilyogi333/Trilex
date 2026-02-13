from rest_framework import serializers
from django.contrib.auth import get_user_model

from chat.models import ChatRoom, ChatMessage, ChatParticipant
from accounts.api.serializers import UserSerializer
from chat.services.message_service import MessageService

User = get_user_model()


# ---------------------------------
# HELPER: Resolve Display Name
# ---------------------------------

def resolve_user_display_name(user):
    """
    Priority:
    1. Client → IDVerification.full_name
    2. Lawyer → BarVerification.full_name
    3. Firm → FirmVerification.firm_name
    4. Fallback → email
    """

    if hasattr(user, "client_verification") and user.client_verification:
        return user.client_verification.full_name

    if hasattr(user, "bar_verification") and user.bar_verification:
        return user.bar_verification.full_name

    if hasattr(user, "firm_verification") and user.firm_verification:
        return user.firm_verification.firm_name

    return user.email


# ---------------------------------
# PARTICIPANT
# ---------------------------------

class ChatParticipantSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = ChatParticipant
        fields = (
            "id",
            "user",
            "is_admin",
            "joined_at",
        )

    def get_user(self, obj):
        user = obj.user

        return {
            "id": str(user.id),
            "email": user.email,
            "role": user.role,
            "name": resolve_user_display_name(user),
        }

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
        last = obj.messages.select_related("sender").order_by("-created_at").first()
        if not last:
            return None

        return {
            "id": str(last.id),
            "room_id": str(obj.id),
            "message": last.message,
            "created_at": last.created_at,
            "sender": {
                "id": str(last.sender.id),
                "email": last.sender.email,
                "name": resolve_user_display_name(last.sender),
            }
        }

    def get_unread_count(self, obj):
        user = self.context["request"].user
        return MessageService.get_unread_count(obj, user)


# ---------------------------------
# MESSAGE SERIALIZER (ROOM MESSAGES API)
# ---------------------------------

class ChatMessageSerializer(serializers.ModelSerializer):
    sender = serializers.SerializerMethodField()
    room_id = serializers.UUIDField(source="room.id", read_only=True)

    class Meta:
        model = ChatMessage
        fields = (
            "id",
            "room_id",
            "message",
            "created_at",
            "sender",
        )

    def get_sender(self, obj):
        return {
            "id": str(obj.sender.id),
            "email": obj.sender.email,
            "name": resolve_user_display_name(obj.sender),
        }


# ---------------------------------
# ADD / REMOVE LAWYER
# ---------------------------------

class ModifyParticipantSerializer(serializers.Serializer):
    lawyer_user_id = serializers.UUIDField(required=True)
