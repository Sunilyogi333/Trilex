from django.contrib.contenttypes.models import ContentType
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from notifications.serializers import NotificationActorSerializer

from notifications.models import Notification

class NotificationService:

    @staticmethod
    def create_notification(
        *,
        recipient,
        notification_type,
        title,
        message,
        entity_type=None,
        entity_id=None,
        content_object=None,
        metadata=None,
        actor=None,

    ):
        content_type = None
        object_id = None

        if content_object:
            content_type = ContentType.objects.get_for_model(content_object)
            object_id = content_object.id

        notification = Notification.objects.create(
            recipient=recipient,
            actor=actor,
            type=notification_type,
            title=title,
            message=message,
            entity_type=entity_type,
            entity_id=entity_id,
            metadata=metadata or {},
            content_type=content_type,
            object_id=object_id,
        )

        NotificationService.send_realtime_notification(notification)
        NotificationService.send_unread_count(notification.recipient)

        return notification

    # ----------------------------
    # Real-time WebSocket delivery
    # ----------------------------
    @staticmethod
    def send_realtime_notification(notification):
        channel_layer = get_channel_layer()

        actor_payload = NotificationActorSerializer.build_actor(
            notification.actor
        )

        payload = {
            "type": "notification",
            "notification": {
                "id": str(notification.id),
                "type": notification.type,
                "title": notification.title,
                "message": notification.message,
                "entity_type": notification.entity_type,
                "entity_id": str(notification.entity_id) if notification.entity_id else None,
                "metadata": notification.metadata,
                "is_read": notification.is_read,
                "created_at": notification.created_at.isoformat(),
                "actor": actor_payload,
            }
        }

        async_to_sync(channel_layer.group_send)(
            f"user_{notification.recipient.id}",
            payload
        )

    @staticmethod
    def send_unread_count(user):
        channel_layer = get_channel_layer()

        count = Notification.objects.filter(
            recipient=user,
            is_read=False
        ).count()

        async_to_sync(channel_layer.group_send)(
            f"user_{user.id}",
            {
                "type": "unread_count",
                "count": count
            }
        )
