# clients/api/serializers.py

from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password

from clients.models import IDVerification
from media.api.serializers import ImageSerializer
from media.models import Image



# -------------------------
# Client Signup
# -------------------------
class ClientSignupSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    client_type = serializers.ChoiceField(
        choices=["mobile", "web"]
    )

    def validate_password(self, value):
        validate_password(value)
        return value


# -------------------------
# Client ID Verification
# -------------------------
# clients/api/serializers.py



class IDVerificationSerializer(serializers.ModelSerializer):
    passport_size_photo = serializers.PrimaryKeyRelatedField(
        queryset=Image.objects.all()
    )
    photo_front = serializers.PrimaryKeyRelatedField(
        queryset=Image.objects.all()
    )
    photo_back = serializers.PrimaryKeyRelatedField(
        queryset=Image.objects.all()
    )

    class Meta:
        model = IDVerification
        fields = (
            "full_name",
            "date_of_birth",
            "id_type",
            "passport_size_photo",
            "photo_front",
            "photo_back",
        )



# clients/api/serializers.py


class IDVerificationMeSerializer(serializers.ModelSerializer):
    passport_size_photo = ImageSerializer(read_only=True)
    photo_front = ImageSerializer(read_only=True)
    photo_back = ImageSerializer(read_only=True)

    class Meta:
        model = IDVerification
        fields = (
            "full_name",
            "date_of_birth",
            "id_type",
            "status",
            "rejection_reason",
            "passport_size_photo",
            "photo_front",
            "photo_back",
        )
