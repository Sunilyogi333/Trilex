from django.db import transaction
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter

from base.constants.user_roles import UserRoles
from base.constants.verification import VerificationStatus
from accounts.permissions import IsFirmUser
from accounts.services.auth_service import AuthService

from firms.models import Firm, FirmVerification
from firms.api.serializers import (
    FirmSignupSerializer,
    FirmProfileUpdateSerializer,
    FirmMeSerializer,
    FirmPublicSerializer,
    FirmAdminSerializer,
)
from firms.services.firm_profile_service import FirmProfileService
from addresses.services.address_service import AddressService
from base.pagination import DefaultPageNumberPagination

User = get_user_model()


def is_admin_user(user):
    return user.is_authenticated and user.role == UserRoles.ADMIN

class FirmSignupView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Firm signup",
        description="Create a firm account and submit initial verification details.",
        request=FirmSignupSerializer,
        responses={
            201: OpenApiResponse(
                description="Firm created and verification submitted"
            ),
            400: OpenApiResponse(description="Email already registered"),
        },
        tags=["firms"],
    )
    @transaction.atomic
    def post(self, request):
        serializer = FirmSignupSerializer(data=request.data)
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
            role=UserRoles.FIRM,
            is_email_verified=False,
        )
                
        address = AddressService.create(address_data)


        firm = Firm.objects.create(
            user=user,
            address=address,
        )        
        firm.services.set(services)

        FirmVerification.objects.create(
            user=user,
            status=VerificationStatus.PENDING,
            **verification_data
        )

        AuthService.send_signup_verification(
            user=user,
            client_type=data["client_type"]
        )

        return Response(
            {"message": "Firm signup successful. Please verify your email."},
            status=201
        )

class FirmMeView(APIView):
    permission_classes = [IsAuthenticated, IsFirmUser]

    @extend_schema(
        summary="Get my firm profile",
        description="Returns authenticated firm's user info, profile and verification status.",
        responses={200: FirmMeSerializer},
        tags=["firms"],
    )
    def get(self, request):
        firm = (
            Firm.objects
            .select_related("address", "user__firm_verification")
            .prefetch_related("services")
            .get(user=request.user)
        )

        serializer = FirmMeSerializer({
            "user": request.user,
            "profile": firm,
            "verification": getattr(request.user, "firm_verification", None),
        })
        return Response(serializer.data)


class FirmProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated, IsFirmUser]

    @extend_schema(
        summary="Update firm profile",
        description="Update firm profile fields like phone number, address, or services.",
        request=FirmProfileUpdateSerializer,
        responses={
            200: OpenApiResponse(description="Profile updated successfully")
        },
        tags=["firms"],
    )
    def patch(self, request):
        firm = request.user.firm_profile

        serializer = FirmProfileUpdateSerializer(
            firm, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)

        FirmProfileService.update_profile(firm, serializer.validated_data)

        return Response({"message": "Profile updated successfully"})


class FirmListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="List firms",
        description=(
            "Public users see only verified firms. "
            "Admins see all firms with full verification details. "
            "Supports searching by firm name and filtering by services, province, and district."
        ),
        parameters=[
            OpenApiParameter(name="page", type=int, location=OpenApiParameter.QUERY),
            OpenApiParameter(name="page_size", type=int, location=OpenApiParameter.QUERY),
            OpenApiParameter(
                name="search",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Search firms by firm name",
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
        ],
        responses={200: FirmPublicSerializer(many=True)},
        tags=["firms"],
    )
    def get(self, request):
        admin = is_admin_user(request.user)

        search = request.query_params.get("search")
        services = request.query_params.get("services")
        province = request.query_params.get("province")
        district = request.query_params.get("district")

        qs = (
            Firm.objects
            .select_related(
                "user",
                "address",
                "user__firm_verification",
            )
            .prefetch_related("services")
        )

        # 🔐 Visibility
        if not admin:
            qs = qs.filter(
                user__firm_verification__status=VerificationStatus.VERIFIED
            )
            serializer_class = FirmPublicSerializer
        else:
            serializer_class = FirmAdminSerializer

        # 🔍 Search by firm name
        if search:
            qs = qs.filter(
                user__firm_verification__firm_name__icontains=search
            )

        # 🧑‍⚖️ Filter by services (UUID-safe)
        if services:
            qs = qs.filter(
                services__id__in=services.split(",")
            )

        # 📍 Filter by province
        if province:
            qs = qs.filter(address__province_id=province)

        # 📍 Filter by district
        if district:
            qs = qs.filter(address__district_id=district)

        # ⚠️ Avoid duplicates from M2M joins
        qs = qs.distinct()

        paginator = DefaultPageNumberPagination()
        page = paginator.paginate_queryset(qs, request)

        data = [
            {
                "user": firm.user,
                "profile": firm,
                "verification": getattr(firm.user, "firm_verification", None),
            }
            for firm in page
        ]

        serializer = serializer_class(data, many=True)
        return paginator.get_paginated_response(serializer.data)


class FirmDetailView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Get firm details",
        description=(
            "Public users can view only verified firms. "
            "Admins can view all firms with full verification data."
        ),
        responses={
            200: FirmPublicSerializer
        },
        tags=["firms"],
    )
    def get(self, request, firm_id):
        admin = is_admin_user(request.user)
        qs = Firm.objects.select_related(
            "user",
            "address",
            "user__firm_verification",
        ).prefetch_related("services")

        if not admin:
            firm = get_object_or_404(
                qs,
                id=firm_id,
                user__firm_verification__status=VerificationStatus.VERIFIED
            )
            serializer_class = FirmPublicSerializer
        else:
            firm = get_object_or_404(qs, id=firm_id)
            serializer_class = FirmAdminSerializer


        serializer = serializer_class({
            "user": firm.user,
            "profile": firm,
            "verification": getattr(firm.user, "firm_verification", None),
        })
        return Response(serializer.data)
