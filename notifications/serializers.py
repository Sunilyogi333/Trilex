from rest_framework import serializers
from notifications.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    actor = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "id",
            "type",
            "title",
            "message",
            "entity_type",
            "entity_id",
            "metadata",
            "is_read",
            "created_at",
            "actor",  # NEW
        ]
        read_only_fields = fields

    def get_actor(self, obj):
        return NotificationActorSerializer.build_actor(obj.actor)


class NotificationActorSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    email = serializers.EmailField(read_only=True)
    name = serializers.CharField(read_only=True)
    role = serializers.CharField(read_only=True)

    @staticmethod
    def build_actor(user):
        if not user:
            return None

        name = user.email

        if hasattr(user, "client_verification") and user.client_verification:
            name = user.client_verification.full_name
        elif hasattr(user, "bar_verification") and user.bar_verification:
            name = user.bar_verification.full_name
        elif hasattr(user, "firm_verification") and user.firm_verification:
            name = user.firm_verification.firm_name

        return {
            "id": user.id,
            "email": user.email,
            "name": name,
            "role": user.role,
        }
