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
from base.constants.case import CaseLawyerRole


class CaseLawyerAssignView(APIView):
    """
    Assign a lawyer to a firm-owned case.
    """

    permission_classes = [IsAuthenticated, CanAssignCaseLawyers]

    @extend_schema(
        summary="Assign lawyer to case",
        description=(
            "Assign a lawyer to a firm-owned case.\n\n"
            "**Rules & Constraints:**\n"
            "- Only firm admin who owns the case can assign lawyers\n"
            "- Lawyer must be a member of the firm\n"
            "- Lawyer can be assigned only once per case\n\n"
            "**Important:**\n"
            "- All assigned lawyers have equal power\n"
            "- Role is automatically set to 'assistant'\n"
            "- can_edit is automatically set to True"
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

        # Ensure case is firm-owned
        if not case.owner_firm:
            return Response(
                {"error": "Only firm-owned cases can have assigned lawyers"},
                status=400
            )

        # Ensure lawyer belongs to firm
        FirmMember.objects.get(
            firm=case.owner_firm,
            lawyer=lawyer
        )

        # Prevent duplicate assignment
        if CaseLawyer.objects.filter(case=case, lawyer=lawyer).exists():
            return Response(
                {"error": "Lawyer already assigned to this case"},
                status=400
            )

        # Auto-assign role + permissions
        CaseLawyer.objects.create(
            case=case,
            lawyer=lawyer,
            role=CaseLawyerRole.ASSISTANT,
            can_edit=True,
        )

        return Response(
            {"message": "Lawyer assigned successfully"},
            status=201
        )
