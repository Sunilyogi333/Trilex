from rest_framework import serializers

from firms.models import FirmMember
from .invitation_serializers import LawyerPublicForInvitationSerializer


class FirmMemberSerializer(serializers.ModelSerializer):
    lawyer = LawyerPublicForInvitationSerializer(
        read_only=True
    )

    class Meta:
        model = FirmMember
        fields = [
            "id",
            "joined_at",
            "lawyer",
        ]
