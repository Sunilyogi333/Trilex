from rest_framework import serializers

from cases.models import CaseClient


class CaseClientCreateSerializer(serializers.ModelSerializer):
    """
    Snapshot of client details for a case.
    Required at case creation.
    """

    class Meta:
        model = CaseClient
        fields = (
            "full_name",
            "address",
            "email",
            "phone",
            "date_of_birth",
            "citizenship_number",
            "gender",
        )


class CaseClientSerializer(serializers.ModelSerializer):
    """
    Read serializer for case client.
    """

    class Meta:
        model = CaseClient
        fields = (
            "id",
            "full_name",
            "address",
            "email",
            "phone",
            "date_of_birth",
            "citizenship_number",
            "gender",
            "created_at",
        )
