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
from base.constants.case import CaseDocumentScope
from base.pagination import DefaultPageNumberPagination


class CaseDocumentCreateView(APIView):
    permission_classes = [IsAuthenticated, CanUploadCaseDocument]

    @extend_schema(
        summary="Upload a case document",
        description=(
            "Upload a document to a case.\n\n"
            "**Document scope:**\n"
            "- internal → lawyer / firm working file\n"
            "- client → client-related evidence or files\n\n"
            "**Client visibility:**\n"
            "- Clients can only see documents they uploaded themselves"
        ),
        parameters=[
            OpenApiParameter(
                name="case_id",
                type=str,
                location=OpenApiParameter.PATH,
            ),
        ],
        request=CaseDocumentCreateSerializer,
        responses={
            201: CaseDocumentSerializer,
            400: OpenApiResponse(description="Validation error"),
            403: OpenApiResponse(description="Permission denied"),
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
    List documents of a case with role-based visibility and pagination.
    """

    permission_classes = [IsAuthenticated, CanViewCaseDocuments]

    @extend_schema(
        summary="List case documents",
        description=(
            "Retrieve documents associated with a case.\n\n"
            "**Scope filters (optional):**\n"
            "- my → documents uploaded by the current user\n"
            "- client → client-related documents\n"
            "- firm → internal firm / lawyer documents\n\n"
            "**Visibility rules:**\n"
            "- Clients see only documents they uploaded\n"
            "- Lawyers and firm admins see documents based on scope\n\n"
            "**Pagination:**\n"
            "- page\n"
            "- page_size"
        ),
        parameters=[
            OpenApiParameter(name="case_id", type=str, location=OpenApiParameter.PATH),
            OpenApiParameter(
                name="scope",
                type=str,
                location=OpenApiParameter.QUERY,
                description="my | client | firm",
            ),
            OpenApiParameter(name="page", type=int, location=OpenApiParameter.QUERY),
            OpenApiParameter(name="page_size", type=int, location=OpenApiParameter.QUERY),
        ],
        responses={
            200: CaseDocumentSerializer(many=True),
            403: OpenApiResponse(description="Permission denied"),
        },
        tags=["cases"],
    )
    def get(self, request, case_id):
        case = get_object_or_404(Case, id=case_id)
        self.check_object_permissions(request, case)

        user = request.user
        scope = request.query_params.get("scope")

        queryset = case.documents.all().order_by("-created_at")

        # -------------------------
        # Client visibility (strict)
        # -------------------------
        if user.role == UserRoles.CLIENT:
            queryset = queryset.filter(
                uploaded_by_type="client",
                uploaded_by_user=user
            )

        # -------------------------
        # Lawyer / Firm visibility
        # -------------------------
        else:
            if scope == "my":
                queryset = queryset.filter(uploaded_by_user=user)

            elif scope == "client":
                queryset = queryset.filter(document_scope="client")

            elif scope == "firm":
                # 🚨 firm scope only valid for firm-owned cases
                if case.owner_type != UserRoles.FIRM:
                    queryset = queryset.none()
                else:
                    queryset = queryset.exclude(uploaded_by_user=user)

            # scope=None → show all allowed documents (default behavior)

        # -------------------------
        # Pagination
        # -------------------------
        paginator = DefaultPageNumberPagination()
        page = paginator.paginate_queryset(queryset, request)

        serializer = CaseDocumentSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
