from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model

from lawyers.models import Lawyer
from cases.models import CaseCategory
from addresses.api.serializers import (
    AddressInputSerializer,
    AddressSerializer,
)
from .verification_serializers import (
    BarVerificationInputSerializer,
    BarVerificationMeSerializer,
    LawyerPublicVerificationSerializer,
    LawyerAdminVerificationSerializer,
)

User = get_user_model()


class LawyerUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "role")

class LawyerServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseCategory
        fields = ("id", "name")

class LawyerProfileSerializer(serializers.ModelSerializer):
    services = LawyerServiceSerializer(many=True)
    address = AddressSerializer(read_only=True)

    class Meta:
        model = Lawyer
        fields = (
            "phone_number",
            "address",
            "services",
        )

class LawyerProfileUpdateSerializer(serializers.Serializer):
    phone_number = serializers.CharField(required=False)

    address = AddressInputSerializer(required=False)

    services = serializers.PrimaryKeyRelatedField(
        queryset=CaseCategory.objects.all(),
        many=True,
        required=False,
    )

    def validate_services(self, value):
        if value is not None and not value:
            raise serializers.ValidationError(
                "At least one service is required."
            )
        return value

class LawyerSignupSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    client_type = serializers.ChoiceField(choices=["mobile", "web"])

    address = AddressInputSerializer()

    services = serializers.PrimaryKeyRelatedField(
        queryset=CaseCategory.objects.all(),
        many=True
    )

    verification = BarVerificationInputSerializer()

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate_services(self, value):
        if not value:
            raise serializers.ValidationError(
                "At least one service is required."
            )
        return value

class LawyerPublicSerializer(serializers.Serializer):
    id = serializers.UUIDField(source="profile.id", read_only=True)
    user = LawyerUserSerializer()
    profile = LawyerProfileSerializer()
    verification = LawyerPublicVerificationSerializer()


class LawyerAdminSerializer(serializers.Serializer):
    id = serializers.UUIDField(source="profile.id", read_only=True)
    user = LawyerUserSerializer()
    profile = LawyerProfileSerializer()
    verification = LawyerAdminVerificationSerializer(allow_null=True)

class LawyerMeSerializer(serializers.Serializer):
    id = serializers.UUIDField(source="profile.id", read_only=True)
    user = LawyerUserSerializer()
    profile = LawyerProfileSerializer()
    verification = BarVerificationMeSerializer(allow_null=True)

class LawyerDashboardSerializer(serializers.Serializer):
    total_cases = serializers.IntegerField()
    total_ongoing_cases = serializers.IntegerField()
    total_pending_bookings = serializers.IntegerField()
    cases_per_month = serializers.ListField(
        child=serializers.DictField()
    )
