from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from drf_spectacular.utils import extend_schema

from accounts.api.serializers import (
    SignupSerializer,
    VerifyOTPSerializer,
    TokenSerializer,
    LoginSerializer,
    EmailSerializer,
    ForgotPasswordVerifyOTPSerializer,
    ResetPasswordSerializer
)
from accounts.services.auth_service import AuthService

class SignupView(APIView):
    permission_classes = [AllowAny]
    @extend_schema(
        request=SignupSerializer,
        responses={200: dict},
        tags=["auth"]
    )

    def post(self, request):
        s = SignupSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data, status = AuthService.signup(**s.validated_data)
        return Response(data, status=status)


class SignupMobileView(APIView):
    permission_classes = [AllowAny]
    @extend_schema(
        request=SignupSerializer,
        responses={201: dict},
        tags=["auth"]
    )

    def post(self, request):
        s = SignupSerializer(data=request.data)
        print(request.data)
        s.is_valid(raise_exception=True)
        data, status = AuthService.signup_mobile(**s.validated_data)
        return Response(data, status=status)


class SignupWebView(APIView):
    permission_classes = [AllowAny]
    @extend_schema(
        request=SignupSerializer,
        responses={200: dict},
        tags=["auth"]
    )
    
    def post(self, request):
        s = SignupSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data, status = AuthService.signup_web(**s.validated_data)
        return Response(data, status=status)


class VerifyOTPView(APIView):
    permission_classes = [AllowAny]
    @extend_schema(
            request=VerifyOTPSerializer,
            responses={200:dict},
            tags=["auth"]
    )

    def post(self, request):
        s = VerifyOTPSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        success, msg = AuthService.verify_otp(**s.validated_data)
        return Response({"message": msg}, status=200 if success else 400)


class VerifyLinkView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=TokenSerializer,
        responses={200: dict},
        tags=["auth"]
    )

    def post(self, request):
        s = TokenSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        success, msg = AuthService.verify_link(s.validated_data["token"])
        return Response({"message": msg})


class LoginView(APIView):
    permission_classes = [AllowAny]
    @extend_schema(
        request=LoginSerializer,
        responses={200: dict},
        tags=["auth"]
    )

    def post(self, request):
        s = LoginSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data, status = AuthService.login(**s.validated_data)
        return Response(data, status=status)

class ResendOTPView(APIView):
    permission_classes = [AllowAny]
    @extend_schema(
        request=EmailSerializer,
        responses={200: dict},
        tags=["auth"]
    )

    def post(self, request):
        s = EmailSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data, status = AuthService.resend_otp(**s.validated_data)
        return Response(data, status=status)


class ResendVerificationLinkView(APIView):
    permission_classes = [AllowAny]
    @extend_schema(
        request=EmailSerializer,
        responses={200: dict},
        tags=["auth"]
    )

    def post(self, request):
        s = EmailSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data, status = AuthService.resend_verification_link(**s.validated_data)
        return Response(data, status=status)


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]
    @extend_schema(
        request=EmailSerializer,
        responses={200: dict},
        tags=["auth"]
    )

    def post(self, request):
        s = EmailSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data, status = AuthService.forgot_password(**s.validated_data)
        return Response(data, status=status)


class VerifyForgotPasswordOTPView(APIView):
    permission_classes = [AllowAny]
    @extend_schema(
        request=ForgotPasswordVerifyOTPSerializer,
        responses={200: dict},
        tags=["auth"]
    )

    def post(self, request):
        s = ForgotPasswordVerifyOTPSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data, status = AuthService.verify_forgot_password_otp(**s.validated_data)
        return Response(data, status=status)


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]
    @extend_schema(
        request=ResetPasswordSerializer,
        responses={200: dict},
        tags=["auth"]
    )

    def post(self, request):
        s = ResetPasswordSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data, status = AuthService.reset_password(**s.validated_data)
        return Response(data, status=status)
