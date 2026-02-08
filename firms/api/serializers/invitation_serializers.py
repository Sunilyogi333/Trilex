from rest_framework import serializers

from firms.models import FirmInvitation

from .firm_serializers import FirmUserSerializer
from .verification_serializers import FirmPublicVerificationSerializer
from lawyers.api.serializers import (
    LawyerUserSerializer,
    LawyerPublicVerificationSerializer,
)

from lawyers.models import Lawyer
from firms.models import Firm

class FirmInvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = FirmInvitation
        fields = [
            "id",
            "status",
            "invited_at",
            "responded_at",
        ]
class FirmPublicForInvitationSerializer(serializers.ModelSerializer):
    user = FirmUserSerializer(read_only=True)
    verification = FirmPublicVerificationSerializer(
        source="user.firm_verification",
        read_only=True
    )

    class Meta:
        model = Firm
        fields = (
            "id",
            "user",
            "phone_number",
            "address",
            "services",
            "verification",
        )
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

class FirmSentInvitationListSerializer(serializers.ModelSerializer):
    lawyer = LawyerPublicForInvitationSerializer(read_only=True)

    class Meta:
        model = FirmInvitation
        fields = [
            "id",
            "status",
            "invited_at",
            "responded_at",
            "lawyer",
        ]
        
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

