from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
    OpenApiParameter,
)

from base.pagination import DefaultPageNumberPagination
from notifications.models import Notification
from notifications.serializers import NotificationSerializer
from notifications.services import NotificationService


# LIST NOTIFICATIONS
class NotificationListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List my notifications",
        description=(
            "Returns paginated notifications for the authenticated user. "
            "Results are ordered by newest first. "
            "Supports optional filtering by read status."
        ),
        parameters=[
            OpenApiParameter("page", int, OpenApiParameter.QUERY),
            OpenApiParameter("page_size", int, OpenApiParameter.QUERY),
            OpenApiParameter(
                name="is_read",
                type=bool,
                location=OpenApiParameter.QUERY,
                description="Filter notifications by read/unread status",
            ),
        ],
        responses={200: NotificationSerializer(many=True)},
        operation_id="notifications_list",
        tags=["notifications"],
    )
    def get(self, request):
        qs = Notification.objects.filter(recipient=request.user)

        is_read = request.query_params.get("is_read")
        if is_read is not None:
            qs = qs.filter(is_read=is_read.lower() == "true")

        paginator = DefaultPageNumberPagination()
        page = paginator.paginate_queryset(qs, request)

        serializer = NotificationSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


# MARK SINGLE NOTIFICATION AS READ
class NotificationMarkReadAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Mark notification as read",
        description=(
            "Marks a specific notification as read for the authenticated user. "
            "Triggers a real-time WebSocket unread_count update."
        ),
        responses={
            200: OpenApiResponse(description="Notification marked as read"),
            404: OpenApiResponse(description="Notification not found"),
        },
        operation_id="notifications_mark_read",
        tags=["notifications"],
    )
    def post(self, request, pk):
        notification = get_object_or_404(
            Notification,
            pk=pk,
            recipient=request.user
        )

        if not notification.is_read:
            notification.is_read = True
            notification.save(update_fields=["is_read"])

            # Push updated unread counter via WebSocket
            NotificationService.send_unread_count(request.user)

        return Response({"message": "Notification marked as read"})


# MARK ALL NOTIFICATIONS AS READ
class NotificationBulkMarkReadAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Mark all notifications as read",
        description=(
            "Marks all unread notifications as read for the authenticated user. "
            "Returns number of updated records and triggers real-time unread_count update."
        ),
        responses={
            200: OpenApiResponse(description="All notifications marked as read"),
        },
        operation_id="notifications_mark_all_read",
        tags=["notifications"],
    )
    def post(self, request):
        updated = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).update(is_read=True)

        # Push updated unread counter via WebSocket
        NotificationService.send_unread_count(request.user)

        return Response({
            "message": "All notifications marked as read",
            "updated": updated
        })
