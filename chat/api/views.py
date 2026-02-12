from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema

from chat.models import ChatRoom
from chat.services.room_service import RoomService
from chat.services.message_service import MessageService
from chat.services.participant_service import ParticipantService
from chat.api.serializers import (
    ChatRoomListSerializer,
    ChatMessageSerializer,
    ModifyParticipantSerializer,
)
from base.pagination import DefaultPageNumberPagination


# ==========================================
# CREATE / GET ROOM
# ==========================================

class CreateOrGetRoomView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(tags=["chat"])
    def post(self, request, booking_id):
        room = RoomService.create_or_get_room(
            user=request.user,
            booking_id=booking_id
        )

        serializer = ChatRoomListSerializer(
            room,
            context={"request": request}
        )

        return Response(serializer.data, status=200)


# ==========================================
# LIST MY ROOMS
# ==========================================

class MyChatRoomsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(tags=["chat"])
    def get(self, request):
        rooms = ChatRoom.objects.filter(
            participants__user=request.user
        ).distinct().prefetch_related(
            "participants__user",
            "messages"
        )

        paginator = DefaultPageNumberPagination()
        page = paginator.paginate_queryset(rooms, request)

        serializer = ChatRoomListSerializer(
            page,
            many=True,
            context={"request": request}
        )

        return paginator.get_paginated_response(serializer.data)


# ==========================================
# ROOM MESSAGES
# ==========================================

class RoomMessagesView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(tags=["chat"])
    def get(self, request, room_id):
        room = get_object_or_404(ChatRoom, id=room_id)

        MessageService.validate_room_access(request.user, room)

        messages = room.messages.select_related("sender")

        paginator = DefaultPageNumberPagination()
        page = paginator.paginate_queryset(messages, request)

        serializer = ChatMessageSerializer(page, many=True)

        return paginator.get_paginated_response(serializer.data)


# ==========================================
# MARK AS READ
# ==========================================

class MarkRoomAsReadView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(tags=["chat"])
    def post(self, request, room_id):
        MessageService.mark_room_as_read(room_id, request.user)
        return Response({"message": "Marked as read"}, status=200)


# ==========================================
# ADD LAWYER
# ==========================================

class AddLawyerToRoomView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(tags=["chat"])
    def post(self, request, room_id):
        serializer = ModifyParticipantSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ParticipantService.add_lawyer(
            room_id=room_id,
            request_user=request.user,
            lawyer_user_id=serializer.validated_data["lawyer_user_id"]
        )

        return Response({"message": "Lawyer added successfully"}, status=200)


# ==========================================
# REMOVE LAWYER
# ==========================================

class RemoveLawyerFromRoomView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(tags=["chat"])
    def post(self, request, room_id):
        serializer = ModifyParticipantSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ParticipantService.remove_lawyer(
            room_id=room_id,
            request_user=request.user,
            lawyer_user_id=serializer.validated_data["lawyer_user_id"]
        )

        return Response({"message": "Lawyer removed successfully"}, status=200)
