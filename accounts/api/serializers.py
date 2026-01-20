from rest_framework import serializers

from rest_framework import serializers
from accounts.models import User
from clients.api.serializers import IDVerificationMeSerializer
from lawyers.api.serializers import BarVerificationMeSerializer
from firms.api.serializers import FirmVerificationMeSerializer

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(min_length=6, max_length=6)

    def validate_otp(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("OTP must contain only digits.")
        return value


class TokenSerializer(serializers.Serializer):
    token = serializers.CharField()

class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ForgotPasswordVerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(min_length=6, max_length=6)

    def validate_otp(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("OTP must contain only digits.")
        return value


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=8, write_only=True)

class MeSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.CharField()
    is_email_verified = serializers.BooleanField()

    profile = serializers.SerializerMethodField()
    verification = serializers.SerializerMethodField()

    def get_profile(self, user: User):
        if user.role == "client" and hasattr(user, "client_profile"):
            return {
                "phone_number": user.client_profile.phone_number,
                "address": user.client_profile.address,
            }

        if user.role == "lawyer" and hasattr(user, "lawyer_profile"):
            return {
                "phone_number": user.lawyer_profile.phone_number,
                "address": user.lawyer_profile.address,
            }

        if user.role == "firm" and hasattr(user, "firm_profile"):
            return {
                "phone_number": user.firm_profile.phone_number,
                "address": user.firm_profile.address,
            }

        return None

    def get_verification(self, user: User):
        if user.role == "client" and hasattr(user, "client_verification"):
            return IDVerificationMeSerializer(
                user.client_verification
            ).data

        if user.role == "lawyer" and hasattr(user, "bar_verification"):
            return BarVerificationMeSerializer(
                user.bar_verification
            ).data

        if user.role == "firm" and hasattr(user, "firm_verification"):
            return FirmVerificationMeSerializer(
                user.firm_verification
            ).data

        return None
