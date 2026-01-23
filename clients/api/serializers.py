from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from clients.models import Client, IDVerification
from media.models import Image
from media.api.serializers import ImageSerializer
from addresses.api.serializers import AddressInputSerializer, AddressSerializer
from accounts.api.serializers import UserSerializer


User = get_user_model()

# -------------------------
# USER
# -------------------------
class ClientUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id, email", "role")
        read_only=["id"]

# -------------------------
# PROFILE
# -------------------------
class ClientProfileSerializer(serializers.ModelSerializer):
    address = AddressSerializer(read_only=True)

    class Meta:
        model = Client
        fields = (
            "phone_number",
            "address",
        )



class ClientProfileUpdateSerializer(serializers.Serializer):
    phone_number = serializers.CharField(required=False)
    address = AddressInputSerializer(required=False)


# -------------------------
# VERIFICATION (ME)
# -------------------------
class ClientVerificationStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = IDVerification
        fields = (
            "status",
            "rejection_reason",
        )


# -------------------------
# ME AGGREGATE
# -------------------------



# -------------------------
# SIGNUP
# -------------------------
class ClientSignupSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    client_type = serializers.ChoiceField(choices=["mobile", "web"])

    def validate_password(self, value):
        validate_password(value)
        return value


# -------------------------
# VERIFICATION INPUT
# -------------------------
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


class IDVerificationMeSerializer(serializers.ModelSerializer):
    passport_size_photo = ImageSerializer(read_only=True)
    photo_front = ImageSerializer(read_only=True)
    photo_back = ImageSerializer(read_only=True)

    class Meta:
        model = IDVerification
        fields = (
            "id",
            "full_name",
            "date_of_birth",
            "id_type",
            "status",
            "rejection_reason",
            "passport_size_photo",
            "photo_front",
            "photo_back",
        )

class ClientRejectReasonSerializer(serializers.Serializer):
    rejection_reason = serializers.CharField(required=True)

# -------------------------
# PUBLIC / ADMIN SERIALIZERS
# -------------------------
class ClientPublicVerificationSerializer(serializers.ModelSerializer):
    passport_size_photo = ImageSerializer(read_only=True)

    class Meta:
        model = IDVerification
        fields = (
            "full_name",
            "passport_size_photo",
        )


class ClientAdminVerificationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    passport_size_photo = ImageSerializer(read_only=True)
    photo_front = ImageSerializer(read_only=True)
    photo_back = ImageSerializer(read_only=True)

    class Meta:
        model = IDVerification
        fields = (
            "id",
            "user",
            "full_name",
            "date_of_birth",
            "id_type",
            "status",
            "rejection_reason",
            "passport_size_photo",
            "photo_front",
            "photo_back",
        )

class ClientPublicSerializer(serializers.Serializer):
    user = ClientUserSerializer()
    profile = ClientProfileSerializer()
    verification = ClientPublicVerificationSerializer()


class ClientAdminSerializer(serializers.Serializer):
    user = ClientUserSerializer()
    profile = ClientProfileSerializer()
    verification = ClientAdminVerificationSerializer(allow_null=True)

class ClientMeSerializer(serializers.Serializer):
    user = ClientUserSerializer()
    profile = ClientProfileSerializer()
    verification = IDVerificationMeSerializer(allow_null=True)