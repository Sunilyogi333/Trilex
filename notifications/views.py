from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from base.pagination import DefaultPageNumberPagination
from notifications.models import Notification
from notifications.serializers import NotificationSerializer
from notifications.services import NotificationService


class NotificationListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Notification.objects.filter(recipient=request.user)

        paginator = DefaultPageNumberPagination()
        page = paginator.paginate_queryset(qs, request)

        serializer = NotificationSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

class NotificationMarkReadAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        notification = get_object_or_404(
            Notification,
            pk=pk,
            recipient=request.user
        )

        if not notification.is_read:
            notification.is_read = True
            notification.save(update_fields=["is_read"])

            NotificationService.send_unread_count(request.user)

        return Response({"message": "Notification marked as read"})



class NotificationBulkMarkReadAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        updated = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).update(is_read=True)

        NotificationService.send_unread_count(request.user)

        return Response({
            "message": "All notifications marked as read",
            "updated": updated
        })

