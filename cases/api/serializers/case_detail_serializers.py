from rest_framework import serializers

from cases.models import Case
from cases.api.serializers.case_document_serializers import CaseDocumentSerializer
from cases.api.serializers.case_date_serailizers import CaseDateSerializer
from cases.api.serializers.case_lawyer_serializers import CaseLawyerAssignSerializer

class CaseDetailSerializer(serializers.ModelSerializer):
    documents = CaseDocumentSerializer(many=True, read_only=True)
    dates = CaseDateSerializer(many=True, read_only=True)
    assigned_lawyers = serializers.SerializerMethodField()

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

            # client
            "client_full_name",
            "client_address",
            "client_email",
            "client_phone",
            "client_date_of_birth",
            "client_citizenship_number",
            "client_gender",

            # waris
            "waris_full_name",
            "waris_email",
            "waris_address",
            "waris_phone",
            "waris_date_of_birth",
            "waris_citizenship_number",
            "waris_gender",

            "documents",
            "dates",
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
