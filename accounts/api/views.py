from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from django.contrib.auth import get_user_model

from drf_spectacular.utils import extend_schema, OpenApiResponse

from accounts.api.serializers import (
    LoginSerializer,
    VerifyOTPSerializer,
    TokenSerializer,
    EmailSerializer,
    ForgotPasswordVerifyOTPSerializer,
    ResetPasswordSerializer,
    DevDeleteAccountSerializer
)
from accounts.services.auth_service import AuthService
from rest_framework import status
from django.conf import settings
User = get_user_model()

class LoginView(APIView):
    permission_classes = [AllowAny]
    @extend_schema(
        summary="Login",
        description="Authenticate user and return JWT access and refresh tokens.",
        request=LoginSerializer,
        responses={
            200: OpenApiResponse(
                description="Login successful. Returns access and refresh tokens."
            ),
            400: OpenApiResponse(description="Invalid credentials"),
            403: OpenApiResponse(description="Email not verified"),
        },
        operation_id="auth_login",
        tags=["auth"],
    )

    def post(self, request):
        s = LoginSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data, status = AuthService.login(**s.validated_data)
        return Response(data, status=status)

class VerifyOTPView(APIView):
    permission_classes = [AllowAny]
    @extend_schema(
        summary="Verify signup OTP",
        description="Verify OTP sent to the user's email during signup.",
        request=VerifyOTPSerializer,
        responses={
            200: OpenApiResponse(description="OTP verified successfully"),
            400: OpenApiResponse(description="Invalid or expired OTP"),
        },
        operation_id="auth_verify_otp",
        tags=["auth"],
    )

    def post(self, request):
        s = VerifyOTPSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        success, msg = AuthService.verify_otp(**s.validated_data)
        return Response({"message": msg}, status=200 if success else 400)


class VerifyLinkView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Verify email via link",
        description="Verify user's email using a token sent via email.",
        request=TokenSerializer,
        responses={
            200: OpenApiResponse(description="Email verified successfully"),
            400: OpenApiResponse(description="Invalid or expired token"),
        },
        operation_id="auth_verify_link",
        tags=["auth"],
    )

    def post(self, request):
        s = TokenSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        success, msg = AuthService.verify_link(s.validated_data["token"])
        return Response({"message": msg})

class ResendOTPView(APIView):
    permission_classes = [AllowAny]
    @extend_schema(
        summary="Resend OTP",
        description="Resend signup OTP to the user's email.",
        request=EmailSerializer,
        responses={
            200: OpenApiResponse(description="OTP resent successfully"),
            404: OpenApiResponse(description="User not found"),
        },
        operation_id="auth_resend_otp",
        tags=["auth"],
    )

    def post(self, request):
        s = EmailSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data, status = AuthService.resend_otp(**s.validated_data)
        return Response(data, status=status)


class ResendVerificationLinkView(APIView):
    permission_classes = [AllowAny]
    @extend_schema(
        summary="Resend verification link",
        description="Resend email verification link to the user.",
        request=EmailSerializer,
        responses={
            200: OpenApiResponse(description="Verification link resent successfully"),
            404: OpenApiResponse(description="User not found"),
        },
        operation_id="auth_resend_verification_link",
        tags=["auth"],
    )

    def post(self, request):
        s = EmailSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data, status = AuthService.resend_verification_link(**s.validated_data)
        return Response(data, status=status)


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]
    @extend_schema(
        summary="Forgot password",
        description="Send OTP to user's email for password reset.",
        request=EmailSerializer,
        responses={
            200: OpenApiResponse(description="OTP sent successfully"),
            404: OpenApiResponse(description="User not found"),
        },
        operation_id="auth_forgot_password",
        tags=["auth"],
    )

    def post(self, request):
        s = EmailSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data, status = AuthService.forgot_password(**s.validated_data)
        return Response(data, status=status)


class VerifyForgotPasswordOTPView(APIView):
    permission_classes = [AllowAny]
    @extend_schema(
        summary="Verify forgot password OTP",
        description="Verify OTP and return a password reset token.",
        request=ForgotPasswordVerifyOTPSerializer,
        responses={
            200: OpenApiResponse(
                description="OTP verified successfully. Returns reset token."
            ),
            400: OpenApiResponse(description="Invalid or expired OTP"),
            404: OpenApiResponse(description="User not found"),
        },
        operation_id="auth_verify_forgot_password_otp",
        tags=["auth"],
    )

    def post(self, request):
        s = ForgotPasswordVerifyOTPSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data, status = AuthService.verify_forgot_password_otp(**s.validated_data)
        return Response(data, status=status)


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]
    @extend_schema(
        summary="Reset password",
        description="Reset user password using a valid reset token.",
        request=ResetPasswordSerializer,
        responses={
            200: OpenApiResponse(description="Password reset successfully"),
            400: OpenApiResponse(description="Invalid or expired token"),
            404: OpenApiResponse(description="User not found"),
        },
        operation_id="auth_reset_password",
        tags=["auth"],
    )

    def post(self, request):
        s = ResetPasswordSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data, status = AuthService.reset_password(**s.validated_data)
        return Response(data, status=status)

class DevDeleteAccountView(APIView):
    """
    DEV ONLY
    Deletes a user and all related objects via Django ORM (CASCADE).
    """

    permission_classes = [IsAdminUser]

    @extend_schema(
        summary="DEV ONLY – Delete user account",
        description="Deletes a user and all related objects via Django ORM (CASCADE).",
        request=DevDeleteAccountSerializer,
        responses={
            200: OpenApiResponse(description="User deleted successfully"),
            400: OpenApiResponse(description="Email missing"),
            403: OpenApiResponse(description="Not allowed"),
            404: OpenApiResponse(description="User not found"),
        },
        tags=["dev"],
    )
    def post(self, request):
        serializer = DevDeleteAccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        user.delete()  # ORM cascade happens here

        return Response(
            {"detail": f"User {email} deleted successfully."},
            status=status.HTTP_200_OK,
        )