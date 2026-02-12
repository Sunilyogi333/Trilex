from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
    OpenApiParameter,
)
from drf_spectacular.types import OpenApiTypes

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
from rest_framework.exceptions import APIException


# =====================================================
# CREATE OR GET CHAT ROOM
# =====================================================

class CreateOrGetRoomView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Create or Get Chat Room",
        description="Create a chat room for a booking if it does not exist. Returns existing room if already created.",
        responses={
            200: ChatRoomListSerializer,
            403: OpenApiResponse(description="You are not allowed to access this booking."),
        },
        tags=["chat"],
    )
    def post(self, request, booking_id):
        room = RoomService.create_or_get_room(
            user=request.user,
            booking_id=booking_id,
        )

        serializer = ChatRoomListSerializer(
            room,
            context={"request": request},
        )

        return Response(serializer.data, status=status.HTTP_200_OK)


# =====================================================
# LIST MY CHAT ROOMS (PAGINATED)
# =====================================================

class MyChatRoomsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List My Chat Rooms",
        description="Returns paginated list of chat rooms where the authenticated user is a participant.",
        parameters=[
            OpenApiParameter(
                name="page",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Page number",
            ),
            OpenApiParameter(
                name="page_size",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Number of records per page",
            ),
        ],
        responses={
            200: ChatRoomListSerializer(many=True),
        },
        tags=["chat"],
    )
    def get(self, request):
        qs = ChatRoom.objects.filter(
            participants__user=request.user
        ).distinct().prefetch_related(
            "participants__user"
        )

        paginator = DefaultPageNumberPagination()
        page = paginator.paginate_queryset(qs, request)

        serializer = ChatRoomListSerializer(
            page,
            many=True,
            context={"request": request},
        )

        return paginator.get_paginated_response(serializer.data)


# =====================================================
# ROOM MESSAGES (PAGINATED)
# =====================================================

class RoomMessagesView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get Room Messages",
        description="Returns paginated list of messages in a specific chat room. Only participants can access.",
        parameters=[
            OpenApiParameter(
                name="page",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Page number",
            ),
            OpenApiParameter(
                name="page_size",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Number of messages per page",
            ),
        ],
        responses={
            200: ChatMessageSerializer(many=True),
            403: OpenApiResponse(description="You are not a participant in this room."),
        },
        tags=["chat"],
    )
    def get(self, request, room_id):
        room = get_object_or_404(ChatRoom, id=room_id)

        MessageService.validate_room_access(request.user, room)

        messages = room.messages.select_related("sender").order_by("-created_at")

        paginator = DefaultPageNumberPagination()
        page = paginator.paginate_queryset(messages, request)

        serializer = ChatMessageSerializer(page, many=True)

        return paginator.get_paginated_response(serializer.data)


# =====================================================
# MARK ROOM AS READ
# =====================================================

class MarkRoomAsReadView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Mark Room As Read",
        description="Marks all unread messages in the room as read for the authenticated user.",
        responses={
            200: OpenApiResponse(description="Marked as read successfully"),
            403: OpenApiResponse(description="You are not a participant in this room."),
        },
        tags=["chat"],
    )
    def post(self, request, room_id):
        MessageService.mark_room_as_read(room_id, request.user)
        return Response(
            {"message": "Marked as read"},
            status=status.HTTP_200_OK,
        )


# =====================================================
# ADD LAWYER TO ROOM
# =====================================================

class AddLawyerToRoomView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Add Lawyer To Room",
        description="Adds a lawyer to a firm booking chat room. Only firm admin can perform this action.",
        request=ModifyParticipantSerializer,
        responses={
            200: OpenApiResponse(description="Lawyer added successfully"),
            403: OpenApiResponse(description="Permission denied"),
        },
        tags=["chat"],
    )
    def post(self, request, room_id):
        serializer = ModifyParticipantSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ParticipantService.add_lawyer(
            room_id=room_id,
            request_user=request.user,
            lawyer_user_id=serializer.validated_data["lawyer_user_id"],
        )

        return Response(
            {"message": "Lawyer added successfully"},
            status=status.HTTP_200_OK,
        )


# =====================================================
# REMOVE LAWYER FROM ROOM
# =====================================================

class RemoveLawyerFromRoomView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Remove Lawyer From Room",
        description="Removes a lawyer from a firm booking chat room. Only firm admin can perform this action.",
        request=ModifyParticipantSerializer,
        responses={
            200: OpenApiResponse(description="Lawyer removed successfully"),
            403: OpenApiResponse(description="Permission denied"),
        },
        tags=["chat"],
    )
    def post(self, request, room_id):
        serializer = ModifyParticipantSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ParticipantService.remove_lawyer(
            room_id=room_id,
            request_user=request.user,
            lawyer_user_id=serializer.validated_data["lawyer_user_id"],
        )

        return Response(
            {"message": "Lawyer removed successfully"},
            status=status.HTTP_200_OK,
        )
