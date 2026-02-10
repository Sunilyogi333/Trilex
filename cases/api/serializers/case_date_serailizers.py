from rest_framework import serializers

from cases.models import CaseDate

class CaseDateCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseDate
        fields = (
            "date_type",
            "date",
            "remark",
            "assigned_to_name",
        )

class CaseDateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseDate
        fields = (
            "id",
            "date_type",
            "date",
            "remark",
            "assigned_to_name",
            "created_at",
        )
