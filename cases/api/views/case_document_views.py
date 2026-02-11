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
    permission_classes = [IsAuthenticated, CanViewCaseDocuments]

    @extend_schema(
        summary="List case documents",
        description=(
            "Retrieve documents associated with a case.\n\n"
            "--------------------------------------------\n"
            " VISIBILITY RULES\n"
            "--------------------------------------------\n\n"
            " CLIENT USER:\n"
            "- Always sees ONLY documents they uploaded themselves.\n"
            "- Scope filter is ignored.\n\n"
            " LAWYER /  FIRM ADMIN:\n\n"
            "Optional `scope` query parameter controls filtering:\n\n"
            " scope=my\n"
            "- Returns documents uploaded by the current user\n"
            "- Only documents with scope = internal\n\n"
            " scope=firm\n"
            "- Only valid for firm-owned cases\n"
            "- Returns internal documents uploaded by:\n"
            "  • Other assigned lawyers\n"
            "  • The firm\n"
            "- Excludes current user's uploads\n\n"
            " scope=client\n"
            "- Returns all documents where scope = client\n"
            "- Includes uploads by:\n"
            "  • Client\n"
            "  • Current lawyer\n"
            "  • Other lawyers\n"
            "  • Firm\n\n"
            "If no scope is provided:\n"
            "- All documents visible to the role are returned.\n\n"
            "--------------------------------------------\n"
            " PAGINATION SUPPORTED\n"
            "- page\n"
            "- page_size\n"
        ),
        parameters=[
            OpenApiParameter(
                name="case_id",
                type=str,
                location=OpenApiParameter.PATH,
                description="UUID of the case",
            ),
            OpenApiParameter(
                name="scope",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter by scope: my | firm | client",
            ),
            OpenApiParameter(
                name="page",
                type=int,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="page_size",
                type=int,
                location=OpenApiParameter.QUERY,
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

        user = request.user
        scope = request.query_params.get("scope")

        queryset = case.documents.select_related(
            "uploaded_by_user",
            "file"
        ).order_by("-created_at")

        # CLIENT USER (STRICT VISIBILITY)
        if user.role == UserRoles.CLIENT:
            queryset = queryset.filter(
                uploaded_by_type="client",
                uploaded_by_user=user
            )

        # LAWYER / FIRM ADMIN
        else:

            # MY : My internal documents only
            if scope == "my":
                queryset = queryset.filter(
                    uploaded_by_user=user,
                    document_scope=CaseDocumentScope.INTERNAL
                )

            # CLIENT : All client-scope documents
            elif scope == "client":
                queryset = queryset.filter(
                    document_scope=CaseDocumentScope.CLIENT
                )

            # FIRM : Other lawyers + firm internal docs
            elif scope == "firm":

                # Only valid for firm-owned cases
                if case.owner_type != UserRoles.FIRM:
                    queryset = queryset.none()
                else:
                    queryset = queryset.filter(
                        document_scope=CaseDocumentScope.INTERNAL
                    ).exclude(
                        uploaded_by_user_id=user.id
                    )

            # If scope is None : return all documents

        paginator = DefaultPageNumberPagination()
        page = paginator.paginate_queryset(queryset, request)

        serializer = CaseDocumentSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
