# firms/api/urls.py

from django.urls import path
from firms.api.views import (
    FirmSignupView,
    FirmVerificationView,
    FirmVerificationMeView,
    FirmVerificationListView,
    FirmVerificationActionView,
)

urlpatterns = [
    # signup
    path("signup/", FirmSignupView.as_view()),

    # firm
    path("verification/", FirmVerificationView.as_view()),
    path("verification/me/", FirmVerificationMeView.as_view()),

    # admin
    path("verifications/", FirmVerificationListView.as_view()),
    path(
        "verifications/<uuid:verification_id>/<str:action>/",
        FirmVerificationActionView.as_view()
    ),
]
