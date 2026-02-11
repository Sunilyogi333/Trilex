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


# =========================================================
# CASE CREATE
# =========================================================

class CaseCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Create a case",
        request=CaseCreateSerializer,
        responses={201: CaseDetailSerializer},
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

        # -------------------------
        # Create Case
        # -------------------------
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

        # Snapshot
        CaseClientDetails.objects.create(
            case=case,
            **client_details_data
        )

        if waris_data:
            CaseWaris.objects.create(case=case, **waris_data)

        return Response(
            CaseDetailSerializer(case).data,
            status=201
        )


# =========================================================
# CASE DETAIL
# =========================================================

class CaseDetailView(APIView):
    permission_classes = [IsAuthenticated, CanViewCase]

    @extend_schema(
        summary="Get case details",
        responses={200: CaseDetailSerializer},
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
        request=CaseUpdateSerializer,
        responses={200: CaseDetailSerializer},
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

        # Update base fields
        for field, value in data.items():
            setattr(case, field, value)

        if client_profile is not None:
            case.client = client_profile

        case.save()

        # Update snapshot
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
# CASE LIST (Optimized)
# =========================================================

class CaseListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List cases",
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

        # -------------------------
        # Lawyer
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

        # -------------------------
        # Firm
        # -------------------------
        elif user.role == UserRoles.FIRM:
            firm = Firm.objects.get(user=user)
            qs = qs.filter(owner_firm=firm)

        # -------------------------
        # Client
        # -------------------------
        elif user.role == UserRoles.CLIENT:
            qs = qs.filter(client__user=user)

        else:
            return Response({"error": "Not allowed"}, status=403)

        # -------------------------
        # Filters
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
                Q(client_details__full_name__icontains=search)
            )

        if created_from := request.query_params.get("created_from"):
            qs = qs.filter(created_at__date__gte=created_from)

        if created_to := request.query_params.get("created_to"):
            qs = qs.filter(created_at__date__lte=created_to)

        qs = qs.distinct()

        # Annotate AFTER filtering
        qs = qs.annotate(
            total_documents=Count("documents", distinct=True)
        )

        # Pagination
        paginator = DefaultPageNumberPagination()
        page = paginator.paginate_queryset(
            qs.order_by("-created_at"),
            request
        )

        serializer = CaseDetailSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
