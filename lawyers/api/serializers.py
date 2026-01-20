# lawyers/api/serializers.py

from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from lawyers.models import BarVerification
from media.models import Image
from media.api.serializers import ImageSerializer

# lawyers/api/serializers.py

from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from lawyers.models import BarVerification
from media.models import Image


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
    verification = BarVerificationInputSerializer()

    def validate_password(self, value):
        validate_password(value)
        return value


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

