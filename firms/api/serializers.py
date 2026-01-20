# firms/api/serializers.py

from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password

from firms.models import FirmVerification
from media.api.serializers import ImageSerializer


# firms/api/serializers.py

from media.models import Image
from firms.models import FirmVerification


class FirmVerificationInputSerializer(serializers.ModelSerializer):
    firm_license = serializers.PrimaryKeyRelatedField(
        queryset=Image.objects.all()
    )

    class Meta:
        model = FirmVerification
        fields = (
            "firm_name",
            "owner_name",
            "firm_email",
            "phone_number",
            "firm_id",
            "firm_license",
        )


class FirmSignupSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    client_type = serializers.ChoiceField(choices=["mobile", "web"])
    verification = FirmVerificationInputSerializer()

    def validate_password(self, value):
        validate_password(value)
        return value



class FirmVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = FirmVerification
        fields = (
            "firm_name",
            "owner_name",
            "firm_email",
            "phone_number",
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
            "firm_email",
            "phone_number",
            "firm_id",
            "status",
            "rejection_reason",
            "firm_license",
        )
