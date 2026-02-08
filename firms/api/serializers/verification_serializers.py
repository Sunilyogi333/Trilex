from rest_framework import serializers
from django.contrib.auth import get_user_model

from firms.models import FirmVerification
from media.models import Image
from media.api.serializers import ImageSerializer
from accounts.api.serializers import UserSerializer

User = get_user_model()
   
class FirmVerificationStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = FirmVerification
        fields = (
            "status",
            "rejection_reason",
        )

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

class FirmRejectReasonSerializer(serializers.Serializer):
    rejection_reason = serializers.CharField(required=True)
    
class FirmPublicVerificationSerializer(serializers.ModelSerializer):
    firm_license = ImageSerializer(read_only=True)

    class Meta:
        model = FirmVerification
        fields = (
            "id",
            "firm_name",
            "firm_license",
        )


class FirmAdminVerificationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    firm_license = ImageSerializer(read_only=True)

    class Meta:
        model = FirmVerification
        fields = (
            "id",
            "user",
            "firm_name",
            "owner_name",
            "firm_id",
            "status",
            "rejection_reason",
            "firm_license",
        )