from django.urls import path

from bookings.api.views import (
    BookingCreateAPIView,
    MySentBookingsAPIView,
    MyReceivedBookingsAPIView,
    BookingDetailAPIView,
    BookingAcceptAPIView,
    BookingRejectAPIView,
)

urlpatterns = [
    path("", BookingCreateAPIView.as_view(), name="booking-create"),
    path("sent/", MySentBookingsAPIView.as_view(), name="booking-sent"),
    path("received/", MyReceivedBookingsAPIView.as_view(), name="booking-received"),
    path("<uuid:pk>/", BookingDetailAPIView.as_view(), name="booking-detail"),
    path("<uuid:pk>/accept/", BookingAcceptAPIView.as_view(), name="booking-accept"),
    path("<uuid:pk>/reject/", BookingRejectAPIView.as_view(), name="booking-reject"),
]
