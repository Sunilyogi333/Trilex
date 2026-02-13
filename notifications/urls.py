from django.urls import path
from notifications.views import (
    NotificationListAPIView,
    NotificationMarkReadAPIView,
    NotificationBulkMarkReadAPIView,
)

urlpatterns = [
    path("", NotificationListAPIView.as_view()),
    path("<uuid:pk>/read/", NotificationMarkReadAPIView.as_view()),
    path("mark-all-read/", NotificationBulkMarkReadAPIView.as_view()),
]
