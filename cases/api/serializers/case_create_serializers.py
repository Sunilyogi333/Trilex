from rest_framework import serializers
from cases.models import Case, CaseCategory
from cases.models.case import CourtType, CaseStatus
from clients.models import Client

from cases.api.serializers.case_client_details_serializers import CaseClientDetailsCreateSerializer
from cases.api.serializers.case_waris_serializers import CaseWarisCreateSerializer


class CaseCreateSerializer(serializers.ModelSerializer):
    court_type = serializers.ChoiceField(choices=CourtType.choices)
    status = serializers.ChoiceField(choices=CaseStatus.choices)

    case_category = serializers.PrimaryKeyRelatedField(
        queryset=CaseCategory.objects.all()
    )

    # 🔹 NEW: link to Client profile
    client = serializers.PrimaryKeyRelatedField(
        queryset=Client.objects.all(),
        required=False,
        allow_null=True
    )

    # snapshot data
    client_details = CaseClientDetailsCreateSerializer(required=True)
    waris = CaseWarisCreateSerializer(required=False)

    class Meta:
        model = Case
        fields = (
            "title",
            "case_category",
            "court_type",
            "description",
            "status",
            "client",           # profile link
            "client_details",  # immutable snapshot
            "waris",
        )


class CaseUpdateSerializer(serializers.ModelSerializer):

    court_type = serializers.ChoiceField(
        choices=CourtType.choices,
        required=False
    )

    status = serializers.ChoiceField(
        choices=CaseStatus.choices,
        required=False
    )

    case_category = serializers.PrimaryKeyRelatedField(
        queryset=CaseCategory.objects.all(),
        required=False
    )

    client = serializers.PrimaryKeyRelatedField(
        queryset=Client.objects.all(),
        required=False,
        allow_null=True
    )

    client_details = CaseClientDetailsCreateSerializer(required=False)
    waris = CaseWarisCreateSerializer(required=False)

    class Meta:
        model = Case
        fields = (
            "title",
            "case_category",
            "court_type",
            "description",
            "status",
            "client",
            "client_details",
            "waris",
        )
