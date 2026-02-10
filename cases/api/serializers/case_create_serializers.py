from rest_framework import serializers

from cases.models import Case, CaseCategory
from cases.models.case import CaseOwnerType, CourtType, CaseStatus

from cases.api.serializers.case_client_serializers import CaseClientCreateSerializer
from cases.api.serializers.case_waris_serializers import CaseWarisCreateSerializer
from cases.api.serializers.case_document_serializers import (
    CaseDocumentCreateSerializer,
)
from cases.api.serializers.case_date_serailizers import (
    CaseDateCreateSerializer,
)

class CaseCreateSerializer(serializers.ModelSerializer):
    court_type = serializers.ChoiceField(choices=CourtType.choices)
    status = serializers.ChoiceField(choices=CaseStatus.choices)

    case_category = serializers.PrimaryKeyRelatedField(
        queryset=CaseCategory.objects.all()
    )

    # --- nested snapshots ---
    client = CaseClientCreateSerializer(required=True)
    waris = CaseWarisCreateSerializer(required=False)

    # --- optional nested ---
    documents = CaseDocumentCreateSerializer(
        many=True,
        required=False
    )
    dates = CaseDateCreateSerializer(
        many=True,
        required=False
    )

    class Meta:
        model = Case
        fields = (
            "title",
            "case_category",
            "court_type",
            "description",
            "status",

            # optional system link
            "client_user",

            # nested
            "client",
            "waris",
            "documents",
            "dates",
        )

class CaseUpdateSerializer(serializers.ModelSerializer):
    """
    Update serializer for Case.
    Used ONLY for updating case metadata and snapshots.
    """

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

    # --- editable snapshots ---
    client = CaseClientCreateSerializer(required=False)
    waris = CaseWarisCreateSerializer(required=False)

    class Meta:
        model = Case
        fields = (
            "title",
            "case_category",
            "court_type",
            "description",
            "status",

            "client_user",

            "client",
            "waris",
        )
