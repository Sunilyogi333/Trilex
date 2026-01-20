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
from accounts.permissions import IsLawyerUser, IsAdminUser
from accounts.services.auth_service import AuthService

from lawyers.models import Lawyer, BarVerification
from lawyers.services.verification_service import LawyerVerificationService
from lawyers.services.lawyer_profile_service import LawyerProfileService

from lawyers.api.serializers import (
    LawyerSignupSerializer,
    BarVerificationSerializer,
    BarVerificationMeSerializer,
    LawyerRejectReasonSerializer,
    LawyerMeSerializer,
    LawyerProfileUpdateSerializer,
    LawyerPublicSerializer,
    LawyerAdminSerializer,
    LawyerAdminVerificationSerializer,
)
from addresses.services.address_service import AddressService
from base.pagination import DefaultPageNumberPagination

User = get_user_model()


def is_admin_user(user):
    return user.is_authenticated and user.role == UserRoles.ADMIN


# =========================
# SIGNUP
# =========================
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


# =========================
# ME
# =========================
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


# =========================
# VERIFICATION
# =========================
class BarVerificationView(APIView):
    permission_classes = [IsAuthenticated, IsLawyerUser]

    @extend_schema(
        summary="Submit bar verification",
        description="Submit or resubmit lawyer bar verification details.",
        request=BarVerificationSerializer,
        responses={
            201: OpenApiResponse(description="Verification submitted")
        },
        tags=["lawyer-verifications"],
    )
    def post(self, request):
        serializer = BarVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        verification = LawyerVerificationService.submit(
            user=request.user,
            **serializer.validated_data
        )

        return Response(
            {"message": "Bar verification submitted", "status": verification.status},
            status=201
        )


class BarVerificationMeView(APIView):
    permission_classes = [IsAuthenticated, IsLawyerUser]

    @extend_schema(
        summary="Get my verification status",
        description="Returns the lawyer's bar verification details and current status.",
        responses={200: BarVerificationMeSerializer},
        tags=["lawyer-verifications"],
    )
    def get(self, request):
        verification = getattr(request.user, "bar_verification", None)
        if not verification:
            return Response(
                {"status": VerificationStatus.NOT_SUBMITTED},
                status=200
            )

        serializer = BarVerificationMeSerializer(verification)
        return Response(serializer.data)


# =========================
# ADMIN: VERIFICATION LIST & ACTIONS
# =========================
class BarVerificationListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    @extend_schema(
        summary="List lawyer verifications (admin)",
        description="Admin-only endpoint to list lawyer verifications with optional status filter.",
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
        responses={200: LawyerAdminVerificationSerializer(many=True)},
        tags=["lawyer-verifications"],
    )
    def get(self, request):
        qs = BarVerification.objects.select_related("user")

        status = request.query_params.get("status")
        if status:
            qs = qs.filter(status=status)

        paginator = DefaultPageNumberPagination()
        page = paginator.paginate_queryset(qs, request)

        serializer = LawyerAdminVerificationSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

class BarVerificationActionView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    @extend_schema(
        summary="Approve or reject lawyer verification",
        description=(
            "Admin-only endpoint to approve or reject a lawyer bar verification. "
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
        request=LawyerRejectReasonSerializer,
        responses={
            200: OpenApiResponse(description="Action completed"),
            400: OpenApiResponse(description="Invalid action"),
        },
        operation_id="lawyer_verification_action",
        tags=["lawyer-verifications"],
    )
    def post(self, request, verification_id, action):
        verification = get_object_or_404(BarVerification, id=verification_id)

        if action == "approve":
            LawyerVerificationService.approve(verification)
            return Response(
                {"message": "Lawyer verified successfully"},
                status=200
            )

        if action == "reject":
            serializer = LawyerRejectReasonSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            LawyerVerificationService.reject(
                verification,
                serializer.validated_data["rejection_reason"],
            )
            return Response(
                {"message": "Lawyer verification rejected"},
                status=200
            )

        return Response({"error": "Invalid action"}, status=400)


# =========================
# LIST & DETAIL
# =========================
class LawyerListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="List lawyers",
        description=(
            "Public users see only verified lawyers with limited verification data. "
            "Admins see all lawyers with full verification details."
        ),
        parameters=[
            OpenApiParameter("page", int, OpenApiParameter.QUERY),
            OpenApiParameter("page_size", int, OpenApiParameter.QUERY),
        ],
        responses={200: LawyerPublicSerializer(many=True)},
        operation_id="lawyers_list",
            tags=["lawyers"],
    )
    def get(self, request):
        admin = is_admin_user(request.user)

        qs = Lawyer.objects.select_related(
            "user",
            "address",
            "user__bar_verification",
        ).prefetch_related("services")

        if not admin:
            qs = qs.filter(
                user__bar_verification__status=VerificationStatus.VERIFIED
            )
            serializer_class = LawyerPublicSerializer
        else:
            serializer_class = LawyerAdminSerializer

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
