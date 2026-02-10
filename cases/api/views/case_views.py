from django.db import transaction
from django.shortcuts import get_object_or_404
from django.db.models import Q

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
    OpenApiParameter,
)

from base.constants.user_roles import UserRoles
from cases.models import Case, CaseLawyer
from cases.api.serializers import (
    CaseCreateSerializer,
    CaseUpdateSerializer,
    CaseDetailSerializer,
)
from cases.permissions import CanViewCase, CanEditCase
from lawyers.models import Lawyer
from firms.models import Firm
from base.pagination import DefaultPageNumberPagination

class CaseCreateView(APIView):
    """
    Create a new case (lawyer or firm owned).
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Create a case",
        description=(
            "Create a new legal case.\n\n"
            "**Who can create a case:**\n"
            "- Verified lawyer (creates a solo case)\n"
            "- Verified firm admin (creates a firm-owned case)\n\n"
            "**Behavior:**\n"
            "- Lawyer-created cases are automatically assigned to the lawyer\n"
            "- Firm-created cases can later have multiple lawyers assigned\n"
            "- Client information is stored as a snapshot for legal consistency"
        ),
        request=CaseCreateSerializer,
        responses={
            201: CaseDetailSerializer,
            400: OpenApiResponse(description="Validation error"),
            403: OpenApiResponse(description="Not allowed to create case"),
        },
        tags=["cases"],
    )
    @transaction.atomic
    def post(self, request):
        serializer = CaseCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        data = serializer.validated_data

        if user.role == UserRoles.LAWYER:
            lawyer = Lawyer.objects.get(user=user)

            case = Case.objects.create(
                owner_type="lawyer",
                owner_lawyer=lawyer,
                created_by=user,
                **data
            )

            # Auto-assign lawyer to own case
            CaseLawyer.objects.create(
                case=case,
                lawyer=lawyer,
                role="lead",
                can_edit=True,
            )

        elif user.role == UserRoles.FIRM:
            firm = Firm.objects.get(user=user)

            case = Case.objects.create(
                owner_type="firm",
                owner_firm=firm,
                created_by=user,
                **data
            )
        else:
            return Response(
                {"error": "Not allowed"},
                status=403
            )

        return Response(
            CaseDetailSerializer(case).data,
            status=201
        )


class CaseDetailView(APIView):
    """
    Retrieve case details with role-based access.
    """

    permission_classes = [IsAuthenticated, CanViewCase]

    @extend_schema(
        summary="Get case details",
        description=(
            "Retrieve full details of a case.\n\n"
            "**Who can view:**\n"
            "- Case owner lawyer\n"
            "- Assigned lawyers\n"
            "- Firm admin (for firm-owned cases)\n"
            "- Client (read-only access)\n\n"
            "**Note:**\n"
            "- Client document visibility is restricted automatically"
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
        case = get_object_or_404(Case, id=case_id)
        self.check_object_permissions(request, case)

        return Response(
            CaseDetailSerializer(case).data
        )


class CaseUpdateView(APIView):
    """
    Update case details.
    """

    permission_classes = [IsAuthenticated, CanEditCase]

    @extend_schema(
        summary="Update a case",
        description=(
            "Update editable fields of a case.\n\n"
            "**Who can update:**\n"
            "- Case owner lawyer\n"
            "- Assigned lawyers with edit permission\n\n"
            "**Restrictions:**\n"
            "- Firm admins and clients cannot update case details"
        ),
        parameters=[
            OpenApiParameter(
                name="case_id",
                type=str,
                location=OpenApiParameter.PATH,
                description="UUID of the case",
            ),
        ],
        request=CaseUpdateSerializer,
        responses={
            200: CaseDetailSerializer,
            400: OpenApiResponse(description="Validation error"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Case not found"),
        },
        tags=["cases"],
    )
    def patch(self, request, case_id):
        case = get_object_or_404(Case, id=case_id)
        self.check_object_permissions(request, case)

        serializer = CaseUpdateSerializer(
            case, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            CaseDetailSerializer(case).data
        )

class CaseListView(APIView):
    """
    List cases with role-based visibility and filtering.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List cases",
        description=(
            "Retrieve a list of cases visible to the authenticated user.\n\n"
            "**Visibility by role:**\n"
            "- Lawyer: solo cases + assigned firm cases\n"
            "- Firm admin: all cases created by the firm\n"
            "- Client: cases where the client is linked\n\n"
            "**Supported filters:**\n"
            "- status\n"
            "- case_category\n"
            "- court_type\n"
            "- search (title / client name)\n"
            "- created_from / created_to (date range)"
        ),
        parameters=[
            OpenApiParameter(
                name="status",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter by case status (draft, registered, ongoing, completed)",
            ),
            OpenApiParameter(
                name="case_category",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Case category UUID",
            ),
            OpenApiParameter(
                name="court_type",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Court type (district, high, supreme)",
            ),
            OpenApiParameter(
                name="search",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Search by case title or client full name",
            ),
            OpenApiParameter(
                name="created_from",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter cases created from this date (YYYY-MM-DD)",
            ),
            OpenApiParameter(
                name="created_to",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter cases created up to this date (YYYY-MM-DD)",
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
            200: CaseDetailSerializer(many=True),
            403: OpenApiResponse(description="Authentication required"),
        },
        tags=["cases"],
    )
    def get(self, request):
        user = request.user
        qs = Case.objects.all()

        # -----------------------------
        # ROLE-BASED VISIBILITY
        # -----------------------------
        if user.role == UserRoles.LAWYER:
            lawyer = Lawyer.objects.get(user=user)

            qs = qs.filter(
                Q(owner_lawyer=lawyer) |
                Q(assigned_lawyers__lawyer=lawyer)
            )

        elif user.role == UserRoles.FIRM:
            firm = Firm.objects.get(user=user)
            qs = qs.filter(owner_firm=firm)

        elif user.role == UserRoles.CLIENT:
            qs = qs.filter(client_user=user)

        else:
            return Response({"error": "Not allowed"}, status=403)

        # Avoid duplicates from joins
        qs = qs.distinct()

        # -----------------------------
        # FILTERS
        # -----------------------------
        status_param = request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)

        case_category = request.query_params.get("case_category")
        if case_category:
            qs = qs.filter(case_category_id=case_category)

        court_type = request.query_params.get("court_type")
        if court_type:
            qs = qs.filter(court_type=court_type)

        search = request.query_params.get("search")
        if search:
            qs = qs.filter(
                Q(title__icontains=search) |
                Q(client_full_name__icontains=search)
            )

        created_from = request.query_params.get("created_from")
        if created_from:
            qs = qs.filter(created_at__date__gte=created_from)

        created_to = request.query_params.get("created_to")
        if created_to:
            qs = qs.filter(created_at__date__lte=created_to)

        # -----------------------------
        # PAGINATION
        # -----------------------------
        paginator = DefaultPageNumberPagination()
        page = paginator.paginate_queryset(qs.order_by("-created_at"), request)

        serializer = CaseDetailSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
