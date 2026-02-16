from django.db import transaction
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
    OpenApiParameter,
)

from base.constants.user_roles import UserRoles
from base.constants.verification import VerificationStatus
from accounts.permissions import IsLawyerUser
from accounts.services.auth_service import AuthService

from lawyers.models import Lawyer, BarVerification
from lawyers.services.lawyer_profile_service import LawyerProfileService

from lawyers.api.serializers import (
    LawyerSignupSerializer,
    LawyerMeSerializer,
    LawyerProfileUpdateSerializer,
    LawyerPublicSerializer,
    LawyerAdminSerializer,
)
from addresses.services.address_service import AddressService
from base.pagination import DefaultPageNumberPagination

User = get_user_model()


def is_admin_user(user):
    return user.is_authenticated and user.role == UserRoles.ADMIN

class LawyerSignupView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Lawyer signup",
        description="Create a lawyer account and submit initial bar verification details.",
        request=LawyerSignupSerializer,
        responses={
            201: OpenApiResponse(description="Lawyer created and verification submitted"),
            400: OpenApiResponse(description="Email already registered"),
        },
        tags=["lawyers"],
    )
    @transaction.atomic
    def post(self, request):
        serializer = LawyerSignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        verification_data = data.pop("verification")
        services = data.pop("services")
        address_data = data.pop("address")

        if User.objects.filter(email=data["email"]).exists():
            return Response({"error": "Email already registered"}, status=400)
        
        user = User.objects.create_user(
            email=data["email"],
            password=data["password"],
            role=UserRoles.LAWYER,
            is_email_verified=False,
        )
        
        address = AddressService.create(address_data)
        
        lawyer = Lawyer.objects.create(
            user=user,
            address=address,
        )
        
        lawyer.services.set(services)

        BarVerification.objects.create(
            user=user,
            status=VerificationStatus.PENDING,
            **verification_data
        )

        AuthService.send_signup_verification(
            user=user,
            client_type=data["client_type"]
        )

        return Response(
            {"message": "Lawyer signup successful. Please verify your email."},
            status=201
        )

class LawyerMeView(APIView):
    permission_classes = [IsAuthenticated, IsLawyerUser]

    @extend_schema(
        summary="Get my lawyer profile",
        description="Returns authenticated lawyer's user info, profile and verification status.",
        responses={200: LawyerMeSerializer},
        tags=["lawyers"],
    )
    def get(self, request):
        lawyer = (
            Lawyer.objects
            .select_related("address")
            .prefetch_related("services")
            .get(user=request.user)
        )
        verification = getattr(request.user, "bar_verification", None)

        serializer = LawyerMeSerializer({
            "user": request.user,
            "profile": lawyer,
            "verification": verification,
        })
        return Response(serializer.data)

class LawyerProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated, IsLawyerUser]

    @extend_schema(
        summary="Update lawyer profile",
        description="Update lawyer profile fields like phone number, address, or services.",
        request=LawyerProfileUpdateSerializer,
        responses={
            200: OpenApiResponse(description="Profile updated successfully")
        },
        tags=["lawyers"],
    )
    def patch(self, request):
        lawyer = Lawyer.objects.select_related("address").get(
            user=request.user
        )

        serializer = LawyerProfileUpdateSerializer(
            lawyer, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)

        LawyerProfileService.update_profile(lawyer, serializer.validated_data)

        return Response({"message": "Profile updated successfully"})

class LawyerListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="List lawyers",
        description=(
            "Public users see only verified lawyers with limited verification data. "
            "Admins see all lawyers with full verification details. "
            "Supports filtering by services, province, district, and searching by full name."
        ),
        parameters=[
            OpenApiParameter(name="page", type=int, location=OpenApiParameter.QUERY),
            OpenApiParameter(name="page_size", type=int, location=OpenApiParameter.QUERY),
            OpenApiParameter(
                name="search",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Search lawyers by full name",
            ),
            OpenApiParameter(
                name="services",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Comma-separated CaseCategory IDs",
            ),
            OpenApiParameter(
                name="province",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Province ID",
            ),
            OpenApiParameter(
                name="district",
                type=int,
                location=OpenApiParameter.QUERY,
                description="District ID",
            ),
            OpenApiParameter(
                name="has_firm",
                type=bool,
                location=OpenApiParameter.QUERY,
                description="Filter lawyers by firm association",
            ),
        ],
        responses={200: LawyerPublicSerializer(many=True)},
        tags=["lawyers"],
    )
    def get(self, request):
        admin = is_admin_user(request.user)
        has_firm = request.query_params.get("has_firm")

        search = request.query_params.get("search")
        services = request.query_params.get("services")
        province = request.query_params.get("province")
        district = request.query_params.get("district")

        qs = (
            Lawyer.objects
            .select_related("user", "address", "user__bar_verification")
            .prefetch_related("services")
        )

        # 🔐 Visibility
        if not admin:
            qs = qs.filter(
                user__bar_verification__status=VerificationStatus.VERIFIED
            )
            serializer_class = LawyerPublicSerializer
        else:
            serializer_class = LawyerAdminSerializer

        # 🔍 Search (full name)
        if search:
            qs = qs.filter(
                user__bar_verification__full_name__icontains=search
            )

        # 🧑‍⚖️ Filter by services
        if services:
            qs = qs.filter(services__id__in=services.split(","))

        if has_firm is not None:
            value = has_firm.lower()
        
            if value in ["true", "1", "yes"]:
                qs = qs.filter(firm_membership__isnull=False)
            elif value in ["false", "0", "no"]:
                qs = qs.filter(firm_membership__isnull=True)
        
        
        # 📍 Filter by province
        if province:
            qs = qs.filter(address__province_id=province)

        # 📍 Filter by district
        if district:
            qs = qs.filter(address__district_id=district)

        # ⚠️ Avoid duplicates due to M2M joins
        qs = qs.distinct()

        paginator = DefaultPageNumberPagination()
        page = paginator.paginate_queryset(qs, request)

        data = [
            {
                "user": lawyer.user,
                "profile": lawyer,
                "verification": getattr(lawyer.user, "bar_verification", None),
            }
            for lawyer in page
        ]

        serializer = serializer_class(data, many=True)
        return paginator.get_paginated_response(serializer.data)


class LawyerDetailView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Get lawyer details",
        description=(
            "Public users can view only verified lawyers. "
            "Admins can view all lawyers with full verification data."
        ),
        responses={200: LawyerPublicSerializer},
        operation_id="lawyers_retrieve",
        tags=["lawyers"],
    )
    def get(self, request, lawyer_id):
        admin = is_admin_user(request.user)

        qs = Lawyer.objects.select_related(
            "user",
            "address",
            "user__bar_verification",
        ).prefetch_related("services")


        if not admin:
            lawyer = get_object_or_404(
                qs,
                id=lawyer_id,
                user__bar_verification__status=VerificationStatus.VERIFIED
            )
            serializer_class = LawyerPublicSerializer
        else:
            lawyer = get_object_or_404(qs, id=lawyer_id)
            serializer_class = LawyerAdminSerializer

        serializer = serializer_class({
            "user": lawyer.user,
            "profile": lawyer,
            "verification": getattr(lawyer.user, "bar_verification", None),
        })
        return Response(serializer.data)
