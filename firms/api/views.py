from django.db import transaction
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from drf_spectacular.utils import extend_schema

from base.constants.user_roles import UserRoles
from base.constants.verification import VerificationStatus
from accounts.permissions import IsFirmUser, IsAdminUser
from accounts.services.auth_service import AuthService

from firms.models import Firm, FirmVerification
from firms.api.serializers import (
    FirmSignupSerializer,
    FirmVerificationSerializer,
    FirmVerificationMeSerializer,
    FirmProfileUpdateSerializer,
    FirmMeSerializer,
    FirmPublicSerializer,
    FirmAdminSerializer,
    FirmAdminVerificationSerializer
)
from firms.services.firm_profile_service import FirmProfileService
from firms.services.verification_service import FirmVerificationService

User = get_user_model()


def is_admin_user(user):
    return user.is_authenticated and user.role == UserRoles.ADMIN


# -------------------------
# SIGNUP
# -------------------------
class FirmSignupView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(request=FirmSignupSerializer, responses={201: dict}, tags=["firms"])
    @transaction.atomic
    def post(self, request):
        serializer = FirmSignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        verification_data = data.pop("verification")
        services = data.pop("services")

        if User.objects.filter(email=data["email"]).exists():
            return Response({"error": "Email already registered"}, status=400)

        user = User.objects.create_user(
            email=data["email"],
            password=data["password"],
            role=UserRoles.FIRM,
            is_email_verified=False,
        )

        firm = Firm.objects.create(user=user)
        firm.services.set(services)

        FirmVerification.objects.create(
            user=user,
            status=FirmVerification.Status.PENDING,
            **verification_data
        )

        AuthService.send_signup_verification(
            user=user,
            client_type=data["client_type"]
        )

        return Response(
            {"message": "Firm signup successful. Verification submitted."},
            status=201
        )


# -------------------------
# ME
# -------------------------
class FirmMeView(APIView):
    permission_classes = [IsAuthenticated, IsFirmUser]

    @extend_schema(responses={200: FirmMeSerializer}, tags=["firms"])
    def get(self, request):
        firm = request.user.firm_profile
        verification = FirmVerification.objects.filter(user=request.user).first()

        serializer = FirmMeSerializer({
            "user": request.user,
            "profile": firm,
            "verification": verification,
        })
        return Response(serializer.data)


class FirmProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated, IsFirmUser]

    @extend_schema(request=FirmProfileUpdateSerializer, responses={200: dict}, tags=["firms"])
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

    @extend_schema(request=FirmVerificationSerializer, responses={201: dict}, tags=["firms"])
    def post(self, request):
        serializer = FirmVerificationSerializer(data=request.data)
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

    @extend_schema(responses=FirmVerificationMeSerializer, tags=["firms"])
    def get(self, request):
        verification = FirmVerification.objects.filter(user=request.user).first()
        if not verification:
            return Response({"status": FirmVerification.Status.NOT_SUBMITTED})

        serializer = FirmVerificationMeSerializer(verification)
        return Response(serializer.data)

# -------------------------
# ADMIN: APPROVE / REJECT
# -------------------------
class FirmVerificationActionView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    @extend_schema(tags=["firms"])
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
            reason = request.data.get("reason")
            FirmVerificationService.reject(verification, reason)
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

    @extend_schema(tags=["firms"])
    def get(self, request):
        admin = is_admin_user(request.user)
        qs = Firm.objects.select_related("user").prefetch_related("services")

        if not admin:
            qs = qs.filter(
                user__firm_verification__status=VerificationStatus.VERIFIED
            )
            serializer_class = FirmPublicSerializer
        else:
            serializer_class = FirmAdminSerializer

        data = [
            {
                "user": firm.user,
                "profile": firm,
                "verification": FirmVerification.objects.filter(user=firm.user).first(),
            }
            for firm in qs
        ]

        serializer = serializer_class(data, many=True)
        return Response(serializer.data)

# -------------------------
# ADMIN: LIST VERIFICATIONS
# -------------------------
class FirmVerificationListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    @extend_schema(
        responses={200: FirmAdminVerificationSerializer(many=True)},
        tags=["firms"]
    )
    def get(self, request):
        qs = FirmVerification.objects.select_related("user")

        status = request.query_params.get("status")
        if status:
            qs = qs.filter(status=status)

        serializer = FirmAdminVerificationSerializer(qs, many=True)
        return Response(serializer.data, status=200)


class FirmDetailView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(tags=["firms"])
    def get(self, request, firm_id):
        admin = is_admin_user(request.user)
        qs = Firm.objects.select_related("user").prefetch_related("services")

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

        verification = FirmVerification.objects.filter(user=firm.user).first()

        serializer = serializer_class({
            "user": firm.user,
            "profile": firm,
            "verification": verification,
        })
        return Response(serializer.data)
