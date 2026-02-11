from rest_framework import serializers

from cases.models import CaseClientDetails


class CaseClientDetailsCreateSerializer(serializers.ModelSerializer):
    """
    Snapshot of client details for a case.
    Required at case creation.
    """

    class Meta:
        model = CaseClientDetails
        fields = (
            "full_name",
            "address",
            "email",
            "phone",
            "date_of_birth",
            "citizenship_number",
            "gender",
        )


class CaseClientDetailsSerializer(serializers.ModelSerializer):
    """
    Read serializer for case client.
    """

    class Meta:
        model = CaseClientDetails
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
