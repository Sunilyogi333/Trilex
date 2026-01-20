from rest_framework import serializers
from django.contrib.auth import get_user_model

from firms.models import Firm, FirmVerification
from case.models import CaseCategory
from media.models import Image
from media.api.serializers import ImageSerializer

User = get_user_model()


# -------------------------
# USER
# -------------------------
class FirmUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("email", "role")


# -------------------------
# SERVICES
# -------------------------
class FirmServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseCategory
        fields = ("id", "name")


# -------------------------
# PROFILE
# -------------------------
class FirmProfileSerializer(serializers.ModelSerializer):
    services = FirmServiceSerializer(many=True)

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


# -------------------------
# VERIFICATION (ME)
# -------------------------
class FirmVerificationStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = FirmVerification
        fields = (
            "status",
            "rejection_reason",
        )


# -------------------------
# ME AGGREGATE
# -------------------------
class FirmMeSerializer(serializers.Serializer):
    user = FirmUserSerializer()
    profile = FirmProfileSerializer()
    verification = FirmVerificationStatusSerializer(allow_null=True)


# -------------------------
# SIGNUP
# -------------------------
class FirmVerificationInputSerializer(serializers.ModelSerializer):
    firm_license = serializers.PrimaryKeyRelatedField(
        queryset=Image.objects.all()
    )

    class Meta:
        model = FirmVerification
        fields = (
            "firm_name",
            "owner_name",
            "firm_id",
            "firm_license",
        )


class FirmSignupSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    client_type = serializers.ChoiceField(choices=["mobile", "web"])
    services = serializers.PrimaryKeyRelatedField(
        queryset=CaseCategory.objects.all(),
        many=True
    )
    verification = FirmVerificationInputSerializer()

    def validate_services(self, value):
        if not value:
            raise serializers.ValidationError(
                "At least one service is required."
            )
        return value
    
# -------------------------
# VERIFICATION APIs
# -------------------------
class FirmVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = FirmVerification
        fields = (
            "firm_name",
            "owner_name",
            "firm_id",
            "firm_license",
        )


class FirmVerificationMeSerializer(serializers.ModelSerializer):
    firm_license = ImageSerializer(read_only=True)

    class Meta:
        model = FirmVerification
        fields = (
            "firm_name",
            "owner_name",
            "firm_id",
            "status",
            "rejection_reason",
            "firm_license",
        )


# -------------------------
# PUBLIC / ADMIN LIST & DETAIL
# -------------------------
class FirmPublicVerificationSerializer(serializers.ModelSerializer):
    firm_license = ImageSerializer(read_only=True)

    class Meta:
        model = FirmVerification
        fields = (
            "firm_name",
            "firm_license",
        )


class FirmAdminVerificationSerializer(serializers.ModelSerializer):
    firm_license = ImageSerializer(read_only=True)

    class Meta:
        model = FirmVerification
        fields = (
            "firm_name",
            "owner_name",
            "firm_id",
            "status",
            "rejection_reason",
            "firm_license",
        )


class FirmPublicSerializer(serializers.Serializer):
    user = FirmUserSerializer()
    profile = FirmProfileSerializer()
    verification = FirmPublicVerificationSerializer()


class FirmAdminSerializer(serializers.Serializer):
    user = FirmUserSerializer()
    profile = FirmProfileSerializer()
    verification = FirmAdminVerificationSerializer(allow_null=True)
