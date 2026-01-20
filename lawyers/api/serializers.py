from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model

from lawyers.models import Lawyer, BarVerification
from cases.models import CaseCategory
from media.models import Image
from media.api.serializers import ImageSerializer
from addresses.api.serializers import (
    AddressInputSerializer,
    AddressSerializer,
)

User = get_user_model()


# -------------------------
# USER
# -------------------------
class LawyerUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("email", "role")


# -------------------------
# SERVICES
# -------------------------
class LawyerServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseCategory
        fields = ("id", "name")


# -------------------------
# PROFILE
# -------------------------
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


# -------------------------
# VERIFICATION (ME)
# -------------------------
class LawyerVerificationStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = BarVerification
        fields = (
            "status",
            "rejection_reason",
        )


# -------------------------
# ME AGGREGATE
# -------------------------
class LawyerMeSerializer(serializers.Serializer):
    user = LawyerUserSerializer()
    profile = LawyerProfileSerializer()
    verification = LawyerVerificationStatusSerializer(allow_null=True)


# -------------------------
# SIGNUP
# -------------------------
class BarVerificationInputSerializer(serializers.ModelSerializer):
    license_photo = serializers.PrimaryKeyRelatedField(
        queryset=Image.objects.all()
    )

    class Meta:
        model = BarVerification
        fields = (
            "full_name",
            "date_of_birth",
            "bar_id",
            "gender",
            "license_photo",
        )


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



# -------------------------
# VERIFICATION APIs
# -------------------------
class BarVerificationSerializer(serializers.ModelSerializer):
    license_photo = serializers.PrimaryKeyRelatedField(
        queryset=Image.objects.all()
    )

    class Meta:
        model = BarVerification
        fields = (
            "full_name",
            "date_of_birth",
            "bar_id",
            "gender",
            "license_photo",
        )


class BarVerificationMeSerializer(serializers.ModelSerializer):
    license_photo = ImageSerializer(read_only=True)

    class Meta:
        model = BarVerification
        fields = (
            "full_name",
            "date_of_birth",
            "bar_id",
            "gender",
            "status",
            "rejection_reason",
            "license_photo",
        )


# -------------------------
# PUBLIC / ADMIN LIST & DETAIL
# -------------------------
class LawyerPublicVerificationSerializer(serializers.ModelSerializer):
    license_photo = ImageSerializer(read_only=True)

    class Meta:
        model = BarVerification
        fields = (
            "full_name",
            "license_photo",
        )


class LawyerAdminVerificationSerializer(serializers.ModelSerializer):
    license_photo = ImageSerializer(read_only=True)

    class Meta:
        model = BarVerification
        fields = (
            "full_name",
            "date_of_birth",
            "bar_id",
            "gender",
            "status",
            "rejection_reason",
            "license_photo",
        )


class LawyerPublicSerializer(serializers.Serializer):
    user = LawyerUserSerializer()
    profile = LawyerProfileSerializer()
    verification = LawyerPublicVerificationSerializer()


class LawyerAdminSerializer(serializers.Serializer):
    user = LawyerUserSerializer()
    profile = LawyerProfileSerializer()
    verification = LawyerAdminVerificationSerializer(allow_null=True)
