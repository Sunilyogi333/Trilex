from django.urls import path
from accounts.api.views import (
    VerifyOTPView,
    VerifyLinkView,
    LoginView,
    ResendOTPView,
    ResendVerificationLinkView,
    ForgotPasswordView,
    VerifyForgotPasswordOTPView,
    ResetPasswordView,
    RefreshAccessTokenView
)

urlpatterns = [
    path("login/", LoginView.as_view()),
    path("refresh/", RefreshAccessTokenView.as_view(), name="token_refresh"),
    path("verify-otp/", VerifyOTPView.as_view()),
    path("verify-link/", VerifyLinkView.as_view()),
    path("resend-otp/", ResendOTPView.as_view()),
    path("resend-verification-link/", ResendVerificationLinkView.as_view()),
    path("forgot-password/", ForgotPasswordView.as_view()),
    path("verify-forgot-password-otp/", VerifyForgotPasswordOTPView.as_view()),
    path("reset-password/", ResetPasswordView.as_view()),
]
