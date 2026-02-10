from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
    OpenApiParameter,
)

from cases.models import Case, CaseDate
from cases.api.serializers import (
    CaseDateCreateSerializer,
    CaseDateSerializer,
)
from cases.permissions import CanManageCaseDates


class CaseDateCreateView(APIView):
    """
    Create court-related dates for a case.
    Examples: tarik date, pesi date, or any custom date.
    """

    permission_classes = [IsAuthenticated, CanManageCaseDates]

    @extend_schema(
        summary="Add a case date",
        description=(
            "Add a court-related date to a case. "
            "Only the case owner lawyer or assigned lawyers can add dates. "
            "Firm admins and clients are not allowed.\n\n"
            "**Examples of dates:**\n"
            "- Tarik date (waris presence)\n"
            "- Pesi date (lawyer presence)\n"
            "- Any custom court-related date"
        ),
        parameters=[
            OpenApiParameter(
                name="case_id",
                type=str,
                location=OpenApiParameter.PATH,
                description="UUID of the case",
            ),
        ],
        request=CaseDateCreateSerializer,
        responses={
            201: CaseDateSerializer,
            400: OpenApiResponse(description="Validation error"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Case not found"),
        },
        tags=["cases"],
    )
    def post(self, request, case_id):
        case = get_object_or_404(Case, id=case_id)
        self.check_object_permissions(request, case)

        serializer = CaseDateCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        case_date = CaseDate.objects.create(
            case=case,
            **serializer.validated_data
        )

        return Response(
            CaseDateSerializer(case_date).data,
            status=201
        )
