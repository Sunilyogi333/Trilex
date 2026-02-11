# cases/views.py

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Prefetch

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
    OpenApiParameter,
)

from base.constants.user_roles import UserRoles
from base.pagination import DefaultPageNumberPagination

from cases.models import (
    Case,
    CaseLawyer,
    CaseClientDetails,
    CaseWaris,
)
from cases.api.serializers import (
    CaseCreateSerializer,
    CaseUpdateSerializer,
    CaseDetailSerializer,
)
from cases.permissions import CanViewCase, CanEditCase

from lawyers.models import Lawyer
from firms.models import Firm


# =========================================================
# CASE CREATE
# =========================================================

class CaseCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Create a case",
        description=(
            "Create a new legal case.\n\n"
            "**Who can create:**\n"
            "- Verified lawyers (creates solo case)\n"
            "- Verified firm admins (creates firm-owned case)\n\n"
            "**Behavior:**\n"
            "- Lawyer-created cases are automatically assigned as lead lawyer\n"
            "- Firm-created cases can later have multiple lawyers assigned\n"
            "- Client profile linking is optional\n"
            "- Client details are stored as immutable snapshot\n"
            "- Waris details are optional\n\n"
            "**Important Notes:**\n"
            "- Operation is atomic\n"
            "- Documents are NOT created here (separate API)\n"
            "- Case ownership is automatically derived from logged-in user"
        ),
        request=CaseCreateSerializer,
        responses={
            201: CaseDetailSerializer,
            400: OpenApiResponse(description="Validation error"),
            403: OpenApiResponse(description="Permission denied"),
        },
        tags=["cases"],
    )
    @transaction.atomic
    def post(self, request):
        serializer = CaseCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        client_profile = data.pop("client", None)
        client_details_data = data.pop("client_details")
        waris_data = data.pop("waris", None)

        user = request.user

        if user.role == UserRoles.LAWYER:
            lawyer = Lawyer.objects.select_related("user").get(user=user)

            case = Case.objects.create(
                owner_type=UserRoles.LAWYER,
                owner_lawyer=lawyer,
                created_by=user,
                client=client_profile,
                **data
            )

            CaseLawyer.objects.create(
                case=case,
                lawyer=lawyer,
                role="lead",
                can_edit=True,
            )

        elif user.role == UserRoles.FIRM:
            firm = Firm.objects.select_related("user").get(user=user)

            case = Case.objects.create(
                owner_type=UserRoles.FIRM,
                owner_firm=firm,
                created_by=user,
                client=client_profile,
                **data
            )
        else:
            return Response({"error": "Not allowed"}, status=403)

        CaseClientDetails.objects.create(
            case=case,
            **client_details_data
        )

        if waris_data:
            CaseWaris.objects.create(case=case, **waris_data)

        return Response(CaseDetailSerializer(case).data, status=201)


# =========================================================
# CASE DETAIL
# =========================================================

class CaseDetailView(APIView):
    permission_classes = [IsAuthenticated, CanViewCase]

    @extend_schema(
        summary="Get case details",
        description=(
            "Retrieve complete details of a single case.\n\n"
            "**Who can view:**\n"
            "- Case owner lawyer\n"
            "- Assigned lawyers\n"
            "- Firm admin (for firm-owned cases)\n"
            "- Linked client (read-only access)\n\n"
            "**What is returned:**\n"
            "- Case metadata\n"
            "- Linked client profile ID\n"
            "- Client snapshot details\n"
            "- Waris details (if exists)\n"
            "- All case dates\n"
            "- Total document count\n"
            "- Assigned lawyers with roles & edit permissions\n\n"
            "**Important Notes:**\n"
            "- Documents are NOT embedded\n"
            "- Use Document API to fetch documents\n"
            "- Visibility is strictly enforced"
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
            200: CaseDetailSerializer,
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Case not found"),
        },
        tags=["cases"],
    )
    def get(self, request, case_id):

        case = get_object_or_404(
            Case.objects
            .select_related(
                "owner_lawyer__user",
                "owner_firm__user",
                "client",
                "client_details",
            )
            .prefetch_related(
                Prefetch(
                    "assigned_lawyers",
                    queryset=CaseLawyer.objects.select_related("lawyer__user")
                ),
                "dates",
                "waris",
            )
            .annotate(
                total_documents=Count("documents", distinct=True)
            ),
            id=case_id
        )

        self.check_object_permissions(request, case)

        return Response(CaseDetailSerializer(case).data)


# =========================================================
# CASE UPDATE
# =========================================================

class CaseUpdateView(APIView):
    permission_classes = [IsAuthenticated, CanEditCase]

    @extend_schema(
        summary="Update a case",
        description=(
            "Update editable details of an existing case.\n\n"
            "**Who can update:**\n"
            "- Case owner lawyer\n"
            "- Firm admin (for firm-owned cases)\n"
            "- Assigned lawyers with edit permission\n\n"
            "**Editable fields:**\n"
            "- title\n"
            "- case_category\n"
            "- court_type\n"
            "- description\n"
            "- status\n"
            "- client profile link\n"
            "- client snapshot details\n"
            "- waris details\n\n"
            "**Important Notes:**\n"
            "- Documents cannot be modified here\n"
            "- Dates cannot be modified here\n"
            "- Operation is atomic"
        ),
        request=CaseUpdateSerializer,
        responses={
            200: CaseDetailSerializer,
            400: OpenApiResponse(description="Validation error"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Case not found"),
        },
        tags=["cases"],
    )
    @transaction.atomic
    def patch(self, request, case_id):

        case = get_object_or_404(
            Case.objects.select_related("client_details"),
            id=case_id
        )

        self.check_object_permissions(request, case)

        serializer = CaseUpdateSerializer(
            case,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        client_profile = data.pop("client", None)
        client_details_data = data.pop("client_details", None)
        waris_data = data.pop("waris", None)

        for field, value in data.items():
            setattr(case, field, value)

        if client_profile is not None:
            case.client = client_profile

        case.save()

        if client_details_data:
            CaseClientDetails.objects.update_or_create(
                case=case,
                defaults=client_details_data
            )

        if waris_data:
            CaseWaris.objects.update_or_create(
                case=case,
                defaults=waris_data
            )

        return Response(CaseDetailSerializer(case).data)


# =========================================================
# CASE LIST
# =========================================================

class CaseListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List cases",
        description=(
            "Retrieve a paginated list of cases visible to the authenticated user.\n\n"
            "**Visibility Rules:**\n"
            "- Lawyers: personal + assigned firm cases\n"
            "- Firm admins: all firm-owned cases\n"
            "- Clients: cases linked to their profile\n\n"
            "**Scope Filter (lawyer only):**\n"
            "- personal → only lawyer-owned cases\n"
            "- firm → firm cases assigned to lawyer\n\n"
            "**Supported Filters:**\n"
            "- status\n"
            "- case_category\n"
            "- court_type\n"
            "- search (title or client full name)\n"
            "- created_from (YYYY-MM-DD)\n"
            "- created_to (YYYY-MM-DD)\n\n"
            "**Ordering:**\n"
            "- Newest cases first\n\n"
            "**Response includes:**\n"
            "- Case metadata\n"
            "- Client details\n"
            "- Waris\n"
            "- Dates\n"
            "- total_documents count\n"
            "- Assigned lawyers\n\n"
            "**Notes:**\n"
            "- Results are paginated\n"
            "- Duplicate rows are automatically removed"
        ),
        parameters=[
            OpenApiParameter(name="status", type=str, location=OpenApiParameter.QUERY),
            OpenApiParameter(name="case_category", type=str, location=OpenApiParameter.QUERY),
            OpenApiParameter(name="court_type", type=str, location=OpenApiParameter.QUERY),
            OpenApiParameter(name="search", type=str, location=OpenApiParameter.QUERY),
            OpenApiParameter(
                name="case_scope",
                type=str,
                location=OpenApiParameter.QUERY,
                description="personal | firm (lawyer only)",
            ),
            OpenApiParameter(name="created_from", type=str, location=OpenApiParameter.QUERY),
            OpenApiParameter(name="created_to", type=str, location=OpenApiParameter.QUERY),
            OpenApiParameter(name="page", type=int, location=OpenApiParameter.QUERY),
            OpenApiParameter(name="page_size", type=int, location=OpenApiParameter.QUERY),
        ],
        responses={200: CaseDetailSerializer(many=True)},
        tags=["cases"],
    )
    def get(self, request):

        user = request.user

        qs = Case.objects.select_related(
            "owner_lawyer__user",
            "owner_firm__user",
            "client",
            "client_details",
        ).prefetch_related(
            Prefetch(
                "assigned_lawyers",
                queryset=CaseLawyer.objects.select_related("lawyer__user")
            ),
            "dates",
            "waris",
        )

        case_scope = request.query_params.get("case_scope")

        if user.role == UserRoles.LAWYER:
            lawyer = Lawyer.objects.get(user=user)

            qs = qs.filter(
                Q(owner_lawyer=lawyer) |
                Q(assigned_lawyers__lawyer=lawyer)
            )

            if case_scope == "personal":
                qs = qs.filter(owner_type=UserRoles.LAWYER)

            elif case_scope == "firm":
                qs = qs.filter(owner_type=UserRoles.FIRM)

        elif user.role == UserRoles.FIRM:
            firm = Firm.objects.get(user=user)
            qs = qs.filter(owner_firm=firm)

        elif user.role == UserRoles.CLIENT:
            qs = qs.filter(client__user=user)

        else:
            return Response({"error": "Not allowed"}, status=403)

        if status := request.query_params.get("status"):
            qs = qs.filter(status=status)

        if category := request.query_params.get("case_category"):
            qs = qs.filter(case_category_id=category)

        if court := request.query_params.get("court_type"):
            qs = qs.filter(court_type=court)

        if search := request.query_params.get("search"):
            qs = qs.filter(
                Q(title__icontains=search) |
                Q(client_details__full_name__icontains=search)
            )

        if created_from := request.query_params.get("created_from"):
            qs = qs.filter(created_at__date__gte=created_from)

        if created_to := request.query_params.get("created_to"):
            qs = qs.filter(created_at__date__lte=created_to)

        qs = qs.distinct().annotate(
            total_documents=Count("documents", distinct=True)
        )

        paginator = DefaultPageNumberPagination()
        page = paginator.paginate_queryset(
            qs.order_by("-created_at"),
            request
        )

        serializer = CaseDetailSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
