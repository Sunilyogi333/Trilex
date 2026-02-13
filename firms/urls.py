from django.urls import path
from firms.api.views import (
    FirmSignupView,
    FirmVerificationView,
    FirmVerificationMeView,
    FirmVerificationListView,
    FirmVerificationActionView,
    FirmMeView,
    FirmProfileUpdateView,
    FirmListView,
    FirmDetailView,
    FirmInviteLawyerView,
    FirmSentInvitationsView,
    FirmMembersListView
)
from firms.api.views.dashboard_views import FirmDashboardAPIView

urlpatterns = [
    # signup
    path("signup/", FirmSignupView.as_view()),

    path("dashboard/", FirmDashboardAPIView.as_view(), name="firm-dashboard"),

    # self
    path("me/", FirmMeView.as_view()),
    path("me/profile/", FirmProfileUpdateView.as_view()),

    # verification
    path("verification/", FirmVerificationView.as_view()),
    path("verification/me/", FirmVerificationMeView.as_view()),

    # public
    path("", FirmListView.as_view()),
    path("<uuid:firm_id>/", FirmDetailView.as_view()),

    # admin
    path("verifications/", FirmVerificationListView.as_view()),
    path(
        "verifications/<uuid:verification_id>/<str:action>/",
        FirmVerificationActionView.as_view(),
    ),

    # invitations
    path(
        "me/invite-lawyer/<uuid:lawyer_id>/",
        FirmInviteLawyerView.as_view(),
    ),
    path(
        "me/invitations/",
        FirmSentInvitationsView.as_view(),
    ),

    # members
    path(
        "me/members/",
        FirmMembersListView.as_view(),
    ),

]
