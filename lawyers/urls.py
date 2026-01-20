# lawyers/api/urls.py

from django.urls import path
from lawyers.api.views import (
    LawyerSignupView,
    BarVerificationView,
    BarVerificationMeView,
    BarVerificationListView,
    BarVerificationActionView,
)

urlpatterns = [
    # signup
    path("signup/", LawyerSignupView.as_view()),

    # lawyer
    path("bar-verification/", BarVerificationView.as_view()),
    path("bar-verification/me/", BarVerificationMeView.as_view()),

    # admin
    path("bar-verifications/", BarVerificationListView.as_view()),
    path(
        "bar-verifications/<uuid:verification_id>/<str:action>/",
        BarVerificationActionView.as_view()
    ),
]
