from django.db import transaction
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter

from base.constants.user_roles import UserRoles
from base.constants.verification import VerificationStatus
from accounts.permissions import IsFirmUser, IsAdminUser
from accounts.services.auth_service import AuthService

from firms.models import Firm, FirmVerification
from firms.api.serializers import (
    FirmSignupSerializer,
    FirmVerificationSerializer,
    FirmVerificationMeSerializer,
    FirmRejectReasonSerializer,
    FirmProfileUpdateSerializer,
    FirmMeSerializer,
    FirmPublicSerializer,
    FirmAdminSerializer,
    FirmAdminVerificationSerializer

)
from firms.services.firm_profile_service import FirmProfileService
from firms.services.verification_service import FirmVerificationService
from addresses.services.address_service import AddressService
from base.pagination import DefaultPageNumberPagination

User = get_user_model()


def is_admin_user(user):
    return user.is_authenticated and user.role == UserRoles.ADMIN


# -------------------------
# SIGNUP
# -------------------------
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


# -------------------------
# ME
# -------------------------
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


# -------------------------
# VERIFICATION
# -------------------------
class FirmVerificationView(APIView):
    permission_classes = [IsAuthenticated, IsFirmUser]

    @extend_schema(
        summary="Submit firm verification",
        description="Submit or resubmit firm verification details.",
        request=FirmVerificationSerializer,
        responses={
            201: OpenApiResponse(
                description="Verification submitted"
            )
        },
        tags=["firm-verifications"],
    )
    def post(self, request):
        existing = FirmVerification.objects.filter(user=request.user).first()
    
        serializer = FirmVerificationSerializer(
            instance=existing,
            data=request.data
        )
        serializer.is_valid(raise_exception=True)
    
        verification = FirmVerificationService.submit(
            user=request.user,
            **serializer.validated_data
        )
    
        return Response(
            {"message": "Firm verification submitted", "status": verification.status},
            status=201
        )

class FirmVerificationMeView(APIView):
    permission_classes = [IsAuthenticated, IsFirmUser]

    @extend_schema(
        summary="Get my verification status",
        description="Returns the firm's verification details and current status.",
        responses={200: FirmVerificationMeSerializer},
        tags=["firm-verifications"],
    )
    def get(self, request):
        verification = FirmVerification.objects.filter(user=request.user).first()
        if not verification:
            return Response({"status": VerificationStatus.NOT_SUBMITTED})

        serializer = FirmVerificationMeSerializer(verification)
        return Response(serializer.data)

# -------------------------
# ADMIN: APPROVE / REJECT
# -------------------------
class FirmVerificationActionView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    @extend_schema(
        summary="Approve or reject firm verification",
        description=(
            "Admin-only endpoint to approve or reject a firm verification. "
            "If rejecting, a reason must be provided in the request body."
        ),
        parameters=[
            OpenApiParameter(
                name="action",
                type=str,
                location=OpenApiParameter.PATH,
                enum=["approve", "reject"],
            )
        ],
        request=FirmRejectReasonSerializer,
        responses={
            200: OpenApiResponse(description="Action completed"),
            400: OpenApiResponse(description="Invalid action"),
        },
        operation_id="firm_verification_action",
        tags=["firm-verifications"],
    )
    def post(self, request, verification_id, action):
        verification = get_object_or_404(
            FirmVerification,
            id=verification_id
        )

        if action == "approve":
            FirmVerificationService.approve(verification)
            return Response(
                {"message": "Firm verified successfully"},
                status=200
            )

        if action == "reject":
            serializer = FirmRejectReasonSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            FirmVerificationService.reject(
                verification,
                serializer.validated_data["rejection_reason"],
            )
            return Response(
                {"message": "Firm verification rejected"},
                status=200
            )

        return Response(
            {"error": "Invalid action"},
            status=400
        )


# -------------------------
# LIST & DETAIL
# -------------------------
class FirmListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="List firms",
        description=(
            "Public users see only verified firms. "
            "Admins see all firms with full verification details."
        ),
        parameters=[
            OpenApiParameter("page", int, OpenApiParameter.QUERY),
            OpenApiParameter("page_size", int, OpenApiParameter.QUERY),
        ],
        responses={200: FirmPublicSerializer(many=True)},
        tags=["firms"],
    )
    def get(self, request):
        admin = is_admin_user(request.user)

        qs = (
            Firm.objects
            .select_related(
                "user",
                "address",
                "user__firm_verification",
            )
            .prefetch_related("services")
        )

        if not admin:
            qs = qs.filter(
                user__firm_verification__status=VerificationStatus.VERIFIED
            )
            serializer_class = FirmPublicSerializer
        else:
            serializer_class = FirmAdminSerializer

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


# -------------------------
# ADMIN: LIST VERIFICATIONS
# -------------------------
class FirmVerificationListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    @extend_schema(
        summary="List firm verifications (admin)",
        description="Admin-only endpoint to list firm verifications with optional status filter.",
        parameters=[
            OpenApiParameter(
                name="status",
                type=str,
                location=OpenApiParameter.QUERY,
                enum=[v for v, _ in VerificationStatus.choices],
            ),
            OpenApiParameter("page", int, OpenApiParameter.QUERY),
            OpenApiParameter("page_size", int, OpenApiParameter.QUERY),
        ],
        responses={200: FirmAdminVerificationSerializer(many=True)},
        tags=["firm-verifications"],
    )
    def get(self, request):
        qs = FirmVerification.objects.select_related("user")

        status = request.query_params.get("status")
        if status:
            qs = qs.filter(status=status)

        paginator = DefaultPageNumberPagination()
        page = paginator.paginate_queryset(qs, request)

        serializer = FirmAdminVerificationSerializer(page, many=True)
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
