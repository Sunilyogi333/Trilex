from rest_framework import serializers

from firms.models import FirmMember
from lawyers.api.serializers import LawyerPublicSerializer


class FirmMemberSerializer(serializers.ModelSerializer):
    lawyer = LawyerPublicSerializer(
        read_only=True
    )

    class Meta:
        model = FirmMember
        fields = [
            "id",
            "joined_at",
            "lawyer",
        ]
