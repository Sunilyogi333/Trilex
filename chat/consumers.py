import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from chat.models import ChatRoom, ChatParticipant
from chat.services.message_service import MessageService


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.group_name = f"chat_{self.room_id}"
        self.user = self.scope.get("user")
        print("User:", self.user)

        if not self.user or not self.user.is_authenticated:
            await self.close()
            return

        has_access = await self.validate_participant()

        if not has_access:
            await self.close()
            return

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return
    
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                "error": "Invalid JSON format"
            }))
            return
    
        message_text = data.get("message")
    
        if not message_text:
            return
    
        message = await self.save_message(message_text)
    
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "chat_message",
                "message": message["message"],
                "sender": message["sender"],
                "message_id": message["id"],
                "created_at": message["created_at"],
            }
        )
    
    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def validate_participant(self):
        try:
            room = ChatRoom.objects.get(id=self.room_id)
            return ChatParticipant.objects.filter(
                room=room,
                user=self.user
            ).exists()
        except ChatRoom.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, message_text):
        message = MessageService.create_message(
            room_id=self.room_id,
            sender=self.user,
            message_text=message_text
        )

        return {
            "id": str(message.id),
            "message": message.message,
            "sender": message.sender.email,
            "created_at": message.created_at.isoformat(),
        }
