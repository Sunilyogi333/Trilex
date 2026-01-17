from rest_framework import serializers
from clients.models import ClientIDVerification


class ClientIDVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientIDVerification
        fields = (
            "full_name",
            "date_of_birth",
            "id_type",
            "passport_size_photo",
            "photo_front",
            "photo_back",
        )


class ClientIDVerificationMeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientIDVerification
        fields = (
            "full_name",
            "date_of_birth",
            "id_type",
            "status",
            "rejection_reason",
        )
