# clients/api/urls.py

from django.urls import path

from clients.api.views import (
    ClientSignupView,
    IDVerificationView,
    IDVerificationMeView,
    IDVerificationListView,
    IDVerificationActionView,
)

urlpatterns = [
    # signup
    path("signup/", ClientSignupView.as_view()),

    # client verification
    path("id-verification/", IDVerificationView.as_view()),
    path("id-verification/me/", IDVerificationMeView.as_view()),

    # admin
    path("id-verifications/", IDVerificationListView.as_view()),
    path(
        "id-verifications/<uuid:verification_id>/<str:action>/",
        IDVerificationActionView.as_view()
    ),
]
