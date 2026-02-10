from rest_framework import serializers

from cases.models import Case
from cases.api.serializers.case_date_serailizers import (
    CaseDateSerializer,
)
from cases.api.serializers.case_client_serializers import (
    CaseClientSerializer,
)
from cases.api.serializers.case_waris_serializers import (
    CaseWarisSerializer,
)


class CaseDetailSerializer(serializers.ModelSerializer):
    """
    Full detail serializer for a case.
    Used for case detail view and dashboards.
    """

    # nested read-only relations
    client = CaseClientSerializer(read_only=True)
    waris = CaseWarisSerializer(read_only=True)

    dates = CaseDateSerializer(many=True, read_only=True)
    total_documents = serializers.IntegerField(read_only=True)

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

            # nested snapshots
            "client",
            "waris",

            # relations
            "dates",
            "total_documents",
            "assigned_lawyers",

            "created_at",
            "updated_at",
        )

    def get_assigned_lawyers(self, obj):
        """
        Returns lawyers assigned to the case with role & permissions.
        """
        return [
            {
                "lawyer_id": cl.lawyer.id,
                "email": cl.lawyer.user.email,
                "role": cl.role,
                "can_edit": cl.can_edit,
            }
            for cl in obj.assigned_lawyers.select_related(
                "lawyer__user"
            )
        ]
