from rest_framework import serializers
from django.contrib.auth import get_user_model

from lawyers.models import BarVerification
from media.models import Image
from media.api.serializers import ImageSerializer
from accounts.api.serializers import UserSerializer

User = get_user_model()



class LawyerVerificationStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = BarVerification
        fields = (
            "status",
            "rejection_reason",
        )

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
class LawyerRejectReasonSerializer(serializers.Serializer):
    rejection_reason = serializers.CharField(required=True)

class LawyerPublicVerificationSerializer(serializers.ModelSerializer):
    license_photo = ImageSerializer(read_only=True)

    class Meta:
        model = BarVerification
        fields = (
            "full_name",
            "license_photo",
        )

class LawyerAdminVerificationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    license_photo = ImageSerializer(read_only=True)

    class Meta:
        model = BarVerification
        fields = (
            "id",
            "user",
            "full_name",
            "date_of_birth",
            "bar_id",
            "gender",
            "status",
            "rejection_reason",
            "license_photo",
        )