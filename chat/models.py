from django.conf import settings
from django.db import models

from base.models import AbstractBaseModel
from bookings.models import Booking


User = settings.AUTH_USER_MODEL


class ChatRoom(AbstractBaseModel):
    """
    One booking = One chat room.
    Chat remains accessible even after booking is completed/cancelled.
    """

    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        related_name="chat_room"
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "chat_rooms"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["booking"]),
        ]

    def __str__(self):
        return f"ChatRoom({self.id}) - Booking({self.booking_id})"


class ChatParticipant(AbstractBaseModel):
    """
    Controls room membership.
    Used for group chat when booking is to firm.
    """

    room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name="participants"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="chat_participations"
    )

    is_admin = models.BooleanField(
        default=False,
        help_text="True only for firm admin in firm bookings"
    )

    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chat_participants"
        unique_together = ("room", "user")
        indexes = [
            models.Index(fields=["room"]),
            models.Index(fields=["user"]),
        ]

    def __str__(self):
        return f"{self.user} in Room({self.room_id})"


class ChatMessage(AbstractBaseModel):
    """
    Stores chat messages.
    """

    room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name="messages"
    )

    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sent_messages"
    )

    message = models.TextField()

    class Meta:
        db_table = "chat_messages"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["room"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["sender"]),
        ]

    def __str__(self):
        return f"Message({self.id}) in Room({self.room_id})"


class MessageRead(models.Model):
    """
    Tracks read status per user per message.
    Required for group chat scalability.
    """

    message = models.ForeignKey(
        ChatMessage,
        on_delete=models.CASCADE,
        related_name="read_statuses"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="read_messages"
    )

    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chat_message_reads"
        unique_together = ("message", "user")
        indexes = [
            models.Index(fields=["message"]),
            models.Index(fields=["user"]),
        ]

    def __str__(self):
        return f"MessageRead({self.message_id}) by {self.user}"
