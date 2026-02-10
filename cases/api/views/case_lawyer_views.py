from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
    OpenApiParameter,
)

from cases.models import Case, CaseLawyer
from cases.api.serializers import CaseLawyerAssignSerializer
from cases.permissions import CanAssignCaseLawyers
from firms.models import FirmMember


class CaseLawyerAssignView(APIView):
    """
    Assign a lawyer to a firm-owned case.
    """

    permission_classes = [IsAuthenticated, CanAssignCaseLawyers]

    @extend_schema(
        summary="Assign a lawyer to a case",
        description=(
            "Assign a lawyer to a firm-owned case.\n\n"
            "**Rules & constraints:**\n"
            "- Only the firm owner/admin who created the case can assign lawyers\n"
            "- The lawyer **must be a member of the firm**\n"
            "- A lawyer can be assigned only once per case\n"
            "- Assigned lawyers can collaborate on the case based on permissions\n\n"
            "**Role & permissions:**\n"
            "- You may optionally define the lawyer's role (lead / assistant)\n"
            "- You may control whether the lawyer can edit the case"
        ),
        parameters=[
            OpenApiParameter(
                name="case_id",
                type=str,
                location=OpenApiParameter.PATH,
                description="UUID of the case",
            ),
        ],
        request=CaseLawyerAssignSerializer,
        responses={
            201: OpenApiResponse(description="Lawyer assigned successfully"),
            400: OpenApiResponse(description="Validation error"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(
                description="Case not found or lawyer not part of firm"
            ),
        },
        tags=["cases"],
    )
    def post(self, request, case_id):
        case = get_object_or_404(Case, id=case_id)
        self.check_object_permissions(request, case)

        serializer = CaseLawyerAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        lawyer = serializer.validated_data["lawyer"]

        # Ensure lawyer belongs to the firm that owns the case
        FirmMember.objects.get(
            firm=case.owner_firm,
            lawyer=lawyer
        )

        CaseLawyer.objects.create(
            case=case,
            lawyer=lawyer,
            role=serializer.validated_data.get("role", "assistant"),
            can_edit=serializer.validated_data.get("can_edit", True),
        )

        return Response(
            {"message": "Lawyer assigned successfully"},
            status=201
        )
