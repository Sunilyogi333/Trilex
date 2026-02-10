from django.db import transaction
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count

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
    CaseClient,
    CaseWaris,
    CaseDocument,
    CaseDate,
)
from cases.api.serializers import (
    CaseCreateSerializer,
    CaseUpdateSerializer,
    CaseDetailSerializer,
)
from cases.permissions import CanViewCase, CanEditCase

from lawyers.models import Lawyer
from firms.models import Firm



class CaseCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Create a case",
        description=(
            "Create a new legal case.\n\n"
            "**Who can create:**\n"
            "- Verified lawyers (solo cases)\n"
            "- Verified firm admins (firm-owned cases)\n\n"
            "**Behavior:**\n"
            "- Lawyer-created cases are automatically assigned to the lawyer\n"
            "- Firm-created cases can later have multiple lawyers assigned\n"
            "- Client and waris details are stored as immutable snapshots\n"
            "- Documents and dates are optional and append-only\n\n"
            "**Notes:**\n"
            "- This operation is atomic\n"
            "- Client linking to system user is optional"
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

        data = serializer.validated_data
        client_data = data.pop("client")
        waris_data = data.pop("waris", None)
        documents = data.pop("documents", [])
        dates = data.pop("dates", [])

        user = request.user

        # -------------------------
        # Create case
        # -------------------------
        if user.role == UserRoles.LAWYER:
            lawyer = Lawyer.objects.get(user=user)

            case = Case.objects.create(
                owner_type=UserRoles.LAWYER,
                owner_lawyer=lawyer,
                created_by=user,
                **data
            )

            CaseLawyer.objects.create(
                case=case,
                lawyer=lawyer,
                role="lead",
                can_edit=True,
            )

        elif user.role == UserRoles.FIRM:
            firm = Firm.objects.get(user=user)

            case = Case.objects.create(
                owner_type=UserRoles.FIRM,
                owner_firm=firm,
                created_by=user,
                **data
            )
        else:
            return Response({"error": "Not allowed"}, status=403)

        # -------------------------
        # Client & Waris snapshots
        # -------------------------
        CaseClient.objects.create(case=case, **client_data)

        if waris_data:
            CaseWaris.objects.create(case=case, **waris_data)

        # -------------------------
        # Documents (append-only)
        # -------------------------
        for doc in documents:
            CaseDocument.objects.create(
                case=case,
                uploaded_by_user=user,
                uploaded_by_type=user.role.lower(),
                **doc
            )

        # -------------------------
        # Dates (append-only)
        # -------------------------
        for date in dates:
            CaseDate.objects.create(case=case, **date)

        return Response(
            CaseDetailSerializer(case).data,
            status=201
        )

from django.db.models import Count

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
            "- Client and waris snapshots\n"
            "- All case dates\n"
            "- Total document count\n"
            "- Assigned lawyers and their roles\n\n"
            "**Important notes:**\n"
            "- Documents are NOT embedded; use documents API\n"
            "- Visibility is strictly enforced via permissions"
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
            Case.objects.annotate(
                total_documents=Count("documents", distinct=True)
            ),
            id=case_id
        )

        self.check_object_permissions(request, case)

        return Response(
            CaseDetailSerializer(case).data
        )



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
            "**What can be updated:**\n"
            "- Case metadata (title, category, court type, status, description)\n"
            "- Client snapshot details\n"
            "- Waris snapshot details\n\n"
            "**Special behavior:**\n"
            "- Documents and dates provided in the request are appended\n"
            "- Existing documents and dates are never deleted implicitly\n\n"
            "**Notes:**\n"
            "- Same payload structure as case creation\n"
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
        case = get_object_or_404(Case, id=case_id)
        self.check_object_permissions(request, case)

        serializer = CaseUpdateSerializer(
            case, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        client_data = data.pop("client", None)
        waris_data = data.pop("waris", None)
        # -------------------------
        # Update case core fields
        # -------------------------
        for field, value in data.items():
            setattr(case, field, value)
        case.save()

        # -------------------------
        # Update / create client & waris
        # -------------------------
        if client_data:
            CaseClient.objects.update_or_create(
                case=case,
                defaults=client_data
            )

        if waris_data:
            CaseWaris.objects.update_or_create(
                case=case,
                defaults=waris_data
            )

        return Response(CaseDetailSerializer(case).data)


class CaseListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List cases",
        description=(
            "Retrieve a paginated list of cases visible to the authenticated user.\n\n"
            "**Visibility rules:**\n"
            "- Lawyers: solo cases + assigned firm cases\n"
            "- Firm admins: all cases owned by the firm\n"
            "- Clients: cases where the client is linked\n\n"
            "**Supported filters:**\n"
            "- status\n"
            "- case_category\n"
            "- court_type\n"
            "- search (case title or client full name)\n"
            "- created_from (YYYY-MM-DD)\n"
            "- created_to (YYYY-MM-DD)\n\n"
            "**Ordering:**\n"
            "- Newest cases first\n\n"
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
                             description=(
                                 "Filter lawyer cases:\n"
                                 "- personal → cases owned by the lawyer\n"
                                 "- firm → firm-owned cases assigned to the lawyer"
                             ),),
            OpenApiParameter(name="created_from", type=str, location=OpenApiParameter.QUERY),
            OpenApiParameter(name="created_to", type=str, location=OpenApiParameter.QUERY),
            OpenApiParameter(name="page", type=int, location=OpenApiParameter.QUERY),
            OpenApiParameter(name="page_size", type=int, location=OpenApiParameter.QUERY),
        ],
        responses={
            200: CaseDetailSerializer(many=True),
            403: OpenApiResponse(description="Authentication required"),
        },
        tags=["cases"],
    )
    def get(self, request):
        user = request.user

        qs = Case.objects.annotate(
            total_documents=Count("documents", distinct=True)
        )

        case_scope = request.query_params.get("case_scope")

        # -------------------------
        # Lawyer visibility
        # -------------------------
        if user.role == UserRoles.LAWYER:
            lawyer = Lawyer.objects.get(user=user)

            qs = qs.filter(
                Q(owner_lawyer=lawyer) |
                Q(assigned_lawyers__lawyer=lawyer)
            )

            if case_scope == "personal":
                qs = qs.filter(
                    owner_type=UserRoles.LAWYER,
                    owner_lawyer=lawyer
                )

            elif case_scope == "firm":
                qs = qs.filter(
                    owner_type=UserRoles.FIRM,
                    assigned_lawyers__lawyer=lawyer
                )

        elif user.role == UserRoles.FIRM:
            firm = Firm.objects.get(user=user)
            qs = qs.filter(owner_firm=firm)

        elif user.role == UserRoles.CLIENT:
            qs = qs.filter(client_user=user)

        else:
            return Response({"error": "Not allowed"}, status=403)

        qs = qs.distinct()

        # -------------------------
        # Filters (unchanged)
        # -------------------------
        if status := request.query_params.get("status"):
            qs = qs.filter(status=status)

        if category := request.query_params.get("case_category"):
            qs = qs.filter(case_category_id=category)

        if court := request.query_params.get("court_type"):
            qs = qs.filter(court_type=court)

        if search := request.query_params.get("search"):
            qs = qs.filter(
                Q(title__icontains=search) |
                Q(client__full_name__icontains=search)
            )

        if created_from := request.query_params.get("created_from"):
            qs = qs.filter(created_at__date__gte=created_from)

        if created_to := request.query_params.get("created_to"):
            qs = qs.filter(created_at__date__lte=created_to)

        paginator = DefaultPageNumberPagination()
        page = paginator.paginate_queryset(
            qs.order_by("-created_at"),
            request
        )

        serializer = CaseDetailSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)