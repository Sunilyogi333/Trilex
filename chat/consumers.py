import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from chat.models import ChatParticipant, ChatMessage
from chat.services.message_service import MessageService


# Track online users (simple in-memory presence)
ONLINE_USERS = set()


class SocketConsumer(AsyncWebsocketConsumer):

    # =========================
    # CONNECT
    # =========================
    async def connect(self):
        self.user = self.scope.get("user")

        if not self.user or not self.user.is_authenticated:
            await self.close()
            return

        self.user_group = f"user_{self.user.id}"

        # Mark user online
        ONLINE_USERS.add(str(self.user.id))

        await self.channel_layer.group_add(
            self.user_group,
            self.channel_name
        )

        await self.accept()
        await self.push_unread_count()


    # =========================
    # DISCONNECT
    # =========================
    async def disconnect(self, close_code):
        # Remove user from online set
        ONLINE_USERS.discard(str(self.user.id))

        await self.channel_layer.group_discard(
            self.user_group,
            self.channel_name
        )

    # =========================
    # RECEIVE ROUTER
    # =========================
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

        elif action == "mark_read":
            await self.handle_mark_read(data)

        else:
            await self.send(json.dumps({"error": "Invalid action"}))

    # =========================
    # JOIN ROOM
    # =========================
    async def join_room(self, data):
        room_id = data.get("room_id")
        if not room_id:
            return

        has_access = await self.validate_participant(room_id)
        if not has_access:
            await self.send(json.dumps({"error": "Access denied"}))
            return

        await self.channel_layer.group_add(
            f"chat_{room_id}",
            self.channel_name
        )

        latest_message = await self.get_latest_message(room_id)

        if latest_message and latest_message["sender"]["id"] != str(self.user.id):
            await self.channel_layer.group_send(
                f"user_{latest_message['sender']['id']}",
                {
                    "type": "message_delivered",
                    "room_id": room_id,
                    "message_id": latest_message["id"],
                    "delivered_to": str(self.user.id),
                }
            )

        await self.send(json.dumps({
            "type": "room_joined",
            "room_id": room_id
        }))

    # =========================
    # LEAVE ROOM
    # =========================
    async def leave_room(self, data):
        room_id = data.get("room_id")
        if not room_id:
            return

        await self.channel_layer.group_discard(
            f"chat_{room_id}",
            self.channel_name
        )

        await self.send(json.dumps({
            "type": "room_left",
            "room_id": room_id
        }))

    # =========================
    # SEND MESSAGE
    # =========================
    async def handle_send_message(self, data):
        room_id = data.get("room_id")
        message_text = data.get("message")
        client_temp_id = data.get("client_temp_id")
    
        if not room_id or not message_text:
            return
    
        has_access = await self.validate_participant(room_id)
        if not has_access:
            await self.send(json.dumps({"error": "Access denied"}))
            return
    
        message = await self.save_message(room_id, message_text)
    
        # ACK to sender
        await self.send(json.dumps({
            "type": "message_sent",
            "client_temp_id": client_temp_id,
            "message_id": message["id"],
            "created_at": message["created_at"],
        }))
    
        # Broadcast message to room
        await self.channel_layer.group_send(
            f"chat_{room_id}",
            {
                "type": "chat_message",
                **message
            }
        )
    
        # Sidebar update
        participants = await self.get_room_participants(room_id)
    
        for user_id in participants:
            await self.channel_layer.group_send(
                f"user_{user_id}",
                {
                    "type": "room_updated",
                    "room_id": room_id,
                    "last_message": message,
                }
            )
    
        # =========================
        # DELIVERY LOGIC (FIXED)
        # =========================
        for user_id in participants:
            user_id_str = str(user_id)

            # Only trigger delivered if recipient is online
            if user_id_str != str(self.user.id) and user_id_str in ONLINE_USERS:
                await self.channel_layer.group_send(
                    f"user_{self.user.id}",  # notify sender
                    {
                        "type": "message_delivered",
                        "room_id": room_id,
                        "message_id": message["id"],
                        "delivered_to": user_id_str,
                    }
                )

    # =========================
    # MARK READ
    # =========================
    async def handle_mark_read(self, data):
        room_id = data.get("room_id")
        if not room_id:
            return

        await self.mark_room_read(room_id)

        participants = await self.get_room_participants(room_id)

        for user_id in participants:
            if str(user_id) != str(self.user.id):
                await self.channel_layer.group_send(
                    f"user_{user_id}",
                    {
                        "type": "message_read",
                        "room_id": room_id,
                        "reader_id": str(self.user.id),
                    }
                )

    async def push_unread_count(self):
        from notifications.models import Notification
        from asgiref.sync import sync_to_async
    
        count = await sync_to_async(
            lambda: Notification.objects.filter(
                recipient=self.user,
                is_read=False
            ).count()
        )()
    
        await self.send(json.dumps({
            "type": "unread_count",
            "count": count
        }))

    async def unread_count(self, event):
        await self.send(json.dumps(event))
    

    # =========================
    # SOCKET EVENT SENDERS
    # =========================
    async def chat_message(self, event):
        await self.send(json.dumps({
            "type": "chat_message",
            **event
        }))

    async def message_delivered(self, event):
        await self.send(json.dumps(event))

    async def message_read(self, event):
        await self.send(json.dumps(event))

    async def room_updated(self, event):
        await self.send(json.dumps(event))

    async def notification(self, event):
        await self.send(json.dumps(event))

    # =========================
    # DATABASE HELPERS
    # =========================
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

        sender_name = self.get_sender_display_name(self.user)

        return {
            "id": str(message.id),
            "room_id": str(room_id),
            "message": message.message,
            "created_at": message.created_at.isoformat(),
            "sender": {
                "id": str(message.sender.id),
                "name": sender_name,
                "email": message.sender.email,
            }
        }

    def get_sender_display_name(self, user):
        if hasattr(user, "client_verification") and user.client_verification:
            return user.client_verification.full_name

        if hasattr(user, "bar_verification") and user.bar_verification:
            return user.bar_verification.full_name

        if hasattr(user, "firm_verification") and user.firm_verification:
            return user.firm_verification.firm_name

        return user.email

    @database_sync_to_async
    def get_latest_message(self, room_id):
        message = (
            ChatMessage.objects
            .select_related("sender")
            .filter(room_id=room_id)
            .order_by("-created_at")
            .first()
        )

        if not message:
            return None

        sender_name = self.get_sender_display_name(message.sender)

        return {
            "id": str(message.id),
            "room_id": str(room_id),
            "message": message.message,
            "created_at": message.created_at.isoformat(),
            "sender": {
                "id": str(message.sender.id),
                "name": sender_name,
                "email": message.sender.email,
            }
        }

    @database_sync_to_async
    def get_room_participants(self, room_id):
        return list(
            ChatParticipant.objects.filter(room_id=room_id)
            .values_list("user_id", flat=True)
        )

    @database_sync_to_async
    def mark_room_read(self, room_id):
        MessageService.mark_room_as_read(room_id, self.user)
