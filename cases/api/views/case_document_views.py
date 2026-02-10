from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
    OpenApiParameter,
)

from cases.models import Case, CaseDocument
from cases.api.serializers import (
    CaseDocumentCreateSerializer,
    CaseDocumentSerializer,
)
from cases.permissions import CanUploadCaseDocument, CanViewCaseDocuments
from base.constants.user_roles import UserRoles


class CaseDocumentCreateView(APIView):
    """
    Upload a document to a case.
    """

    permission_classes = [IsAuthenticated, CanUploadCaseDocument]

    @extend_schema(
        summary="Upload a case document",
        description=(
            "Upload a document related to a case.\n\n"
            "**Who can upload:**\n"
            "- Case owner lawyer\n"
            "- Assigned lawyers\n"
            "- Firm admin (for firm cases)\n"
            "- Client (can upload their own documents)\n\n"
            "**Client restriction:**\n"
            "- Client-uploaded documents are only visible to the client and lawyers."
        ),
        parameters=[
            OpenApiParameter(
                name="case_id",
                type=str,
                location=OpenApiParameter.PATH,
                description="UUID of the case",
            ),
        ],
        request=CaseDocumentCreateSerializer,
        responses={
            201: CaseDocumentSerializer,
            400: OpenApiResponse(description="Validation error"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Case not found"),
        },
        tags=["cases"],
    )
    def post(self, request, case_id):
        case = get_object_or_404(Case, id=case_id)
        self.check_object_permissions(request, case)

        serializer = CaseDocumentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user

        if user.role == UserRoles.CLIENT:
            uploaded_by = "client"
        elif user.role == UserRoles.FIRM:
            uploaded_by = "firm"
        else:
            uploaded_by = "lawyer"

        document = CaseDocument.objects.create(
            case=case,
            uploaded_by_type=uploaded_by,
            uploaded_by_user=user,
            **serializer.validated_data
        )

        return Response(
            CaseDocumentSerializer(document).data,
            status=201
        )


class CaseDocumentListView(APIView):
    """
    List documents of a case with role-based visibility.
    """

    permission_classes = [IsAuthenticated, CanViewCaseDocuments]

    @extend_schema(
        summary="List case documents",
        description=(
            "Retrieve documents associated with a case.\n\n"
            "**Visibility rules:**\n"
            "- Lawyers and firm admins see all documents\n"
            "- Clients see **only documents uploaded by themselves**\n\n"
            "This endpoint enforces document-level access control automatically."
        ),
        parameters=[
            OpenApiParameter(
                name="case_id",
                type=str,
                location=OpenApiParameter.PATH,
                description="UUID of the case",
            ),
        ],
        responses={
            200: CaseDocumentSerializer(many=True),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Case not found"),
        },
        tags=["cases"],
    )
    def get(self, request, case_id):
        case = get_object_or_404(Case, id=case_id)
        self.check_object_permissions(request, case)

        queryset = case.documents.all()

        # Client can see only their own uploaded documents
        if request.user == case.client_user:
            queryset = queryset.filter(uploaded_by_type="client")

        serializer = CaseDocumentSerializer(queryset, many=True)
        return Response(serializer.data)
