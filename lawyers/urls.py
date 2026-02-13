from django.urls import path
from lawyers.api.serializers.dashboard_views import LawyerDashboardAPIView
from lawyers.api.views import (
    LawyerSignupView,
    LawyerMeView,
    LawyerProfileUpdateView,
    LawyerListView,
    LawyerDetailView,
    BarVerificationView,
    BarVerificationMeView,
    BarVerificationListView,
    BarVerificationActionView,
    LawyerInvitationsListView,
    LawyerInvitationRespondView,
)

urlpatterns = [
    # SIGNUP
    path("signup/", LawyerSignupView.as_view()),

    path("dashboard/", LawyerDashboardAPIView.as_view(), name="lawyer-dashboard"),

    # SELF (ME)
    path("me/", LawyerMeView.as_view()),
    path("me/profile/", LawyerProfileUpdateView.as_view()),

    # VERIFICATION (LAWYER)
    path("bar-verification/", BarVerificationView.as_view()),
    path("bar-verification/me/", BarVerificationMeView.as_view()),

    # ADMIN (VERIFICATION)
    path("bar-verifications/", BarVerificationListView.as_view()),
    path(
        "bar-verifications/<uuid:verification_id>/<str:action>/",
        BarVerificationActionView.as_view(),
    ),

    #PUBLIC
    path("", LawyerListView.as_view()),
    path("<uuid:lawyer_id>/", LawyerDetailView.as_view()),

    # INVITATIONS
    path(
        "me/invitations/",
        LawyerInvitationsListView.as_view(),
    ),
    path(
        "me/invitations/<uuid:invitation_id>/<str:action>/",
        LawyerInvitationRespondView.as_view(),
    ),
]
