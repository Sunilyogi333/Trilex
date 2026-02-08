from rest_framework import serializers
from lawyers.models import Lawyer
from .verification_serializers import LawyerPublicVerificationSerializer
from .lawyer_serializers import LawyerUserSerializer
from firms.api.serializers.invitation_serializers import FirmPublicForInvitationSerializer
from firms.models import FirmInvitation


class LawyerPublicForInvitationSerializer(serializers.ModelSerializer):
    user = LawyerUserSerializer(read_only=True)
    verification = LawyerPublicVerificationSerializer(
        source="user.bar_verification",
        read_only=True
    )

    class Meta:
        model = Lawyer
        fields = (
            "id",
            "user",
            "phone_number",
            "address",
            "services",
            "verification",
        )
class LawyerReceivedInvitationListSerializer(serializers.ModelSerializer):
    firm = FirmPublicForInvitationSerializer(read_only=True)

    class Meta:
        model = FirmInvitation
        fields = [
            "id",
            "status",
            "invited_at",
            "responded_at",
            "firm",
        ]
