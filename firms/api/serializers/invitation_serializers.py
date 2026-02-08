from rest_framework import serializers

from firms.models import FirmInvitation
from lawyers.api.serializers import LawyerPublicSerializer
from firms.api.serializers.firm_serializers import FirmPublicSerializer


class FirmInvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = FirmInvitation
        fields = [
            "id",
            "status",
            "invited_at",
            "responded_at",
        ]


class FirmInvitationListSerializer(serializers.ModelSerializer):
    firm = FirmPublicSerializer(
        read_only=True
    )
    lawyer = LawyerPublicSerializer(
        read_only=True
    )

    class Meta:
        model = FirmInvitation
        fields = [
            "id",
            "status",
            "invited_at",
            "responded_at",
            "firm",
            "lawyer",
        ]
