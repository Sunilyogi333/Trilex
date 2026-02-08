from rest_framework import serializers
from django.contrib.auth import get_user_model

from firms.models import Firm
from cases.models import CaseCategory
from .verification_serializers import (
    FirmPublicVerificationSerializer,
    FirmAdminVerificationSerializer,
    FirmVerificationInputSerializer,
    FirmVerificationMeSerializer,
)

from addresses.api.serializers import (
    AddressSerializer,
    AddressInputSerializer,
)

User = get_user_model()


class FirmUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "role")


class FirmServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseCategory
        fields = ("id", "name")

class FirmProfileSerializer(serializers.ModelSerializer):
    services = FirmServiceSerializer(many=True)
    address = AddressSerializer()

    class Meta:
        model = Firm
        fields = (
            "phone_number",
            "address",
            "services",
        )

class FirmProfileUpdateSerializer(serializers.ModelSerializer):
    services = serializers.PrimaryKeyRelatedField(
        queryset=CaseCategory.objects.all(),
        many=True,
        required=False,
    )
    address = AddressInputSerializer(required=False)

    class Meta:
        model = Firm
        fields = (
            "phone_number",
            "address",
            "services",
        )

    def validate_services(self, value):
        if value is not None and not value:
            raise serializers.ValidationError(
                "At least one service is required."
            )
        return value

    def validate_address(self, value):
        if not value:
            raise serializers.ValidationError("Address is required.")
        return value

class FirmSignupSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    client_type = serializers.ChoiceField(choices=["mobile", "web"])
    services = serializers.PrimaryKeyRelatedField(
        queryset=CaseCategory.objects.all(),
        many=True
    )
    address = AddressInputSerializer()
    verification = FirmVerificationInputSerializer()

    def validate_services(self, value):
        if not value:
            raise serializers.ValidationError(
                "At least one service is required."
            )
        return value

class FirmPublicSerializer(serializers.Serializer):
    id = serializers.UUIDField(source="profile.id", read_only=True)
    user = FirmUserSerializer()
    profile = FirmProfileSerializer()
    verification = FirmPublicVerificationSerializer()


class FirmAdminSerializer(serializers.Serializer):
    id = serializers.UUIDField(source="profile.id", read_only=True)
    user = FirmUserSerializer()
    profile = FirmProfileSerializer()
    verification = FirmAdminVerificationSerializer(allow_null=True)

class FirmMeSerializer(serializers.Serializer):
    id = serializers.UUIDField(source="profile.id", read_only=True)
    user = FirmUserSerializer()
    profile = FirmProfileSerializer()
    verification = FirmVerificationMeSerializer(allow_null=True)