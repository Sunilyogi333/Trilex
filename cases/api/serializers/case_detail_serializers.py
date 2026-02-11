from rest_framework import serializers
from cases.models import Case
from cases.api.serializers.case_date_serailizers import CaseDateSerializer
from cases.api.serializers.case_client_details_serializers import CaseClientDetailsSerializer
from cases.api.serializers.case_waris_serializers import CaseWarisSerializer
from clients.api.serializers import (
    CaseClientProfileSerializer
)
from cases.api.serializers.case_category_serializers import CaseCategorySerializer



class CaseDetailSerializer(serializers.ModelSerializer):

    client = CaseClientProfileSerializer(read_only=True)

    client_details = CaseClientDetailsSerializer(read_only=True)
    waris = CaseWarisSerializer(read_only=True)

    dates = CaseDateSerializer(many=True, read_only=True)
    total_documents = serializers.IntegerField(read_only=True)

    assigned_lawyers = serializers.SerializerMethodField()

    case_category = CaseCategorySerializer(read_only=True)

    class Meta:
        model = Case
        fields = (
            "id",
            "owner_type",
            "title",
            "case_category",
            "court_type",
            "description",
            "status",

            "client",
            "client_details",
            "waris",

            "dates",
            "total_documents",
            "assigned_lawyers",

            "created_at",
            "updated_at",
        )

    def get_assigned_lawyers(self, obj):
        return [
            {
                "lawyer_id": cl.lawyer.id,
                "email": cl.lawyer.user.email,
                "role": cl.role,
                "can_edit": cl.can_edit,
            }
            for cl in obj.assigned_lawyers.select_related("lawyer__user")
        ]
