from rest_framework import serializers

from cases.models import CaseWaris


class CaseWarisCreateSerializer(serializers.ModelSerializer):
    """
    Snapshot of waris details for a case.
    Optional at case creation.
    """

    class Meta:
        model = CaseWaris
        fields = (
            "full_name",
            "email",
            "address",
            "phone",
            "date_of_birth",
            "citizenship_number",
            "gender",
        )


class CaseWarisSerializer(serializers.ModelSerializer):
    """
    Read serializer for case waris.
    """

    class Meta:
        model = CaseWaris
        fields = (
            "id",
            "full_name",
            "email",
            "address",
            "phone",
            "date_of_birth",
            "citizenship_number",
            "gender",
            "created_at",
        )
