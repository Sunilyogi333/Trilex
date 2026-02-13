from django.urls import path
from clients.api.dashboard_view import ClientDashboardAPIView
from clients.api.views import (
    ClientSignupView,
    ClientMeView,
    ClientProfileUpdateView,
    IDVerificationView,
    IDVerificationMeView,
    IDVerificationListView,
    IDVerificationActionView,
    ClientListView,
    ClientDetailView,
)

urlpatterns = [
    # signup
    path("signup/", ClientSignupView.as_view()),
    
    path("dashboard/", ClientDashboardAPIView.as_view(), name="client-dashboard"),
    
    # self
    path("me/", ClientMeView.as_view()),
    path("me/profile/", ClientProfileUpdateView.as_view()),

    # verification
    path("verification/", IDVerificationView.as_view()),
    path("verification/me/", IDVerificationMeView.as_view()),

    # admin verification
    path("verifications/", IDVerificationListView.as_view()),
    path(
        "verifications/<uuid:verification_id>/<str:action>/",
        IDVerificationActionView.as_view(),
    ),

    # public
    path("", ClientListView.as_view()),
    path("<uuid:client_id>/", ClientDetailView.as_view()),
]
