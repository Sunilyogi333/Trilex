import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from chat.models import ChatRoom, ChatParticipant
from chat.services.message_service import MessageService


class SocketConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.user = self.scope.get("user")

        if not self.user or not self.user.is_authenticated:
            await self.close()
            return

        # Join personal notification group
        self.user_group = f"user_{self.user.id}"
        await self.channel_layer.group_add(
            self.user_group,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.user_group,
            self.channel_name
        )

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(json.dumps({"error": "Invalid JSON"}))
            return

        action = data.get("action")

        if action == "join_room":
            await self.join_room(data)

        elif action == "leave_room":
            await self.leave_room(data)

        elif action == "send_message":
            await self.handle_send_message(data)

        else:
            await self.send(json.dumps({"error": "Invalid action"}))

    # -----------------------
    # JOIN ROOM
    # -----------------------
    async def join_room(self, data):
        room_id = data.get("room_id")

        if not room_id:
            return

        has_access = await self.validate_participant(room_id)

        if not has_access:
            await self.send(json.dumps({"error": "Access denied"}))
            return

        group_name = f"chat_{room_id}"

        await self.channel_layer.group_add(
            group_name,
            self.channel_name
        )

        await self.send(json.dumps({
            "type": "room_joined",
            "room_id": room_id
        }))

    # -----------------------
    # LEAVE ROOM
    # -----------------------
    async def leave_room(self, data):
        room_id = data.get("room_id")

        if not room_id:
            return

        group_name = f"chat_{room_id}"

        await self.channel_layer.group_discard(
            group_name,
            self.channel_name
        )

        await self.send(json.dumps({
            "type": "room_left",
            "room_id": room_id
        }))

    # -----------------------
    # SEND MESSAGE
    # -----------------------
    async def handle_send_message(self, data):
        room_id = data.get("room_id")
        message_text = data.get("message")

        if not room_id or not message_text:
            return

        has_access = await self.validate_participant(room_id)

        if not has_access:
            await self.send(json.dumps({"error": "Access denied"}))
            return

        message = await self.save_message(room_id, message_text)

        group_name = f"chat_{room_id}"

        # Send to room
        await self.channel_layer.group_send(
            group_name,
            {
                "type": "chat_message",
                "room_id": room_id,
                "message": message["message"],
                "sender": message["sender"],
                "message_id": message["id"],
                "created_at": message["created_at"],
            }
        )

        # Notify participants globally
        participants = await self.get_room_participants(room_id)

        for user_id in participants:
            await self.channel_layer.group_send(
                f"user_{user_id}",
                {
                    "type": "new_message_notification",
                    "room_id": room_id,
                    "message_preview": message["message"],
                }
            )

    # -----------------------
    # RECEIVE ROOM MESSAGE
    # -----------------------
    async def chat_message(self, event):
        await self.send(json.dumps(event))

    # -----------------------
    # RECEIVE NOTIFICATION
    # -----------------------
    async def new_message_notification(self, event):
        await self.send(json.dumps(event))

    # -----------------------
    # DATABASE HELPERS
    # -----------------------
    @database_sync_to_async
    def validate_participant(self, room_id):
        return ChatParticipant.objects.filter(
            room_id=room_id,
            user=self.user
        ).exists()

    @database_sync_to_async
    def save_message(self, room_id, message_text):
        message = MessageService.create_message(
            room_id=room_id,
            sender=self.user,
            message_text=message_text
        )

        return {
            "id": str(message.id),
            "message": message.message,
            "sender": message.sender.email,
            "created_at": message.created_at.isoformat(),
        }

    @database_sync_to_async
    def get_room_participants(self, room_id):
        return list(
            ChatParticipant.objects.filter(room_id=room_id)
            .values_list("user_id", flat=True)
        )
