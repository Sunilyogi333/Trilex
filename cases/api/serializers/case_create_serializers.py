from rest_framework import serializers

from cases.models import Case
from cases.models.case import CaseOwnerType, CourtType, CaseStatus
from cases.models import CaseCategory

class CaseCreateSerializer(serializers.ModelSerializer):
    owner_type = serializers.ChoiceField(choices=CaseOwnerType.choices)

    case_category = serializers.PrimaryKeyRelatedField(
        queryset=CaseCategory.objects.all()
    )

    class Meta:
        model = Case
        fields = (
            "owner_type",
            "title",
            "case_category",
            "court_type",
            "description",
            "status",

            # client (required)
            "client_full_name",
            "client_address",
            "client_email",
            "client_phone",
            "client_date_of_birth",
            "client_citizenship_number",
            "client_gender",

            # optional client link
            "client_user",

            # optional waris
            "waris_full_name",
            "waris_email",
            "waris_address",
            "waris_phone",
            "waris_date_of_birth",
            "waris_citizenship_number",
            "waris_gender",
        )

class CaseUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Case
        fields = (
            "title",
            "case_category",
            "court_type",
            "description",
            "status",

            "client_full_name",
            "client_address",
            "client_email",
            "client_phone",
            "client_date_of_birth",
            "client_citizenship_number",
            "client_gender",

            "waris_full_name",
            "waris_email",
            "waris_address",
            "waris_phone",
            "waris_date_of_birth",
            "waris_citizenship_number",
            "waris_gender",
        )
