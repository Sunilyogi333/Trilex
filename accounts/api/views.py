from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from drf_spectacular.utils import extend_schema, OpenApiResponse

from accounts.api.serializers import (
    LoginSerializer,
    VerifyOTPSerializer,
    TokenSerializer,
    EmailSerializer,
    ForgotPasswordVerifyOTPSerializer,
    ResetPasswordSerializer
)
from accounts.services.auth_service import AuthService

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