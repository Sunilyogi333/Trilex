from django.db import transaction
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from drf_spectacular.utils import extend_schema

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
    LawyerMeSerializer,
    LawyerProfileUpdateSerializer,
    LawyerPublicSerializer,
    LawyerAdminSerializer,
    LawyerAdminVerificationSerializer,
)

User = get_user_model()


def is_admin_user(user):
    return user.is_authenticated and user.role == UserRoles.ADMIN


# -------------------------
# SIGNUP
# -------------------------
class LawyerSignupView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(request=LawyerSignupSerializer, responses={201: dict}, tags=["lawyers"])
    @transaction.atomic
    def post(self, request):
        serializer = LawyerSignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        verification_data = data.pop("verification")
        services = data.pop("services")

        if User.objects.filter(email=data["email"]).exists():
            return Response({"error": "Email already registered"}, status=400)

        user = User.objects.create_user(
            email=data["email"],
            password=data["password"],
            role=UserRoles.LAWYER,
            is_email_verified=False,
        )

        lawyer = Lawyer.objects.create(user=user)
        lawyer.services.set(services)

        BarVerification.objects.create(
            user=user,
            status=BarVerification.Status.PENDING,
            **verification_data
        )

        AuthService.send_signup_verification(
            user=user,
            client_type=data["client_type"]
        )

        return Response(
            {"message": "Lawyer signup successful. Verification submitted."},
            status=201
        )


# -------------------------
# ME
# -------------------------
class LawyerMeView(APIView):
    permission_classes = [IsAuthenticated, IsLawyerUser]

    @extend_schema(responses={200: LawyerMeSerializer}, tags=["lawyers"])
    def get(self, request):
        lawyer = request.user.lawyer_profile
        verification = getattr(request.user, "bar_verification", None)

        serializer = LawyerMeSerializer({
            "user": request.user,
            "profile": lawyer,
            "verification": verification,
        })
        return Response(serializer.data)


class LawyerProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated, IsLawyerUser]

    @extend_schema(request=LawyerProfileUpdateSerializer, responses={200: dict}, tags=["lawyers"])
    def patch(self, request):
        lawyer = request.user.lawyer_profile

        serializer = LawyerProfileUpdateSerializer(
            lawyer, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)

        LawyerProfileService.update_profile(lawyer, serializer.validated_data)

        return Response({"message": "Profile updated successfully"})


# -------------------------
# VERIFICATION
# -------------------------
class BarVerificationView(APIView):
    permission_classes = [IsAuthenticated, IsLawyerUser]

    @extend_schema(request=BarVerificationSerializer, responses={201: dict}, tags=["lawyers"])
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

    @extend_schema(responses=BarVerificationMeSerializer, tags=["lawyers"])
    def get(self, request):
        verification = getattr(request.user, "bar_verification", None)
        if not verification:
            return Response(
                {"status": BarVerification.Status.NOT_SUBMITTED},
                status=200
            )

        serializer = BarVerificationMeSerializer(verification)
        return Response(serializer.data)


# -------------------------
# ADMIN: VERIFICATION LIST & ACTIONS
# -------------------------
class BarVerificationListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    @extend_schema(
        responses={200: LawyerAdminVerificationSerializer(many=True)},
        tags=["lawyers"]
    )
    def get(self, request):
        qs = BarVerification.objects.select_related("user")

        status = request.query_params.get("status")
        if status:
            qs = qs.filter(status=status)

        serializer = LawyerAdminVerificationSerializer(qs, many=True)
        return Response(serializer.data)


class BarVerificationActionView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    @extend_schema(tags=["lawyers"])
    def post(self, request, verification_id, action):
        verification = get_object_or_404(BarVerification, id=verification_id)

        if action == "approve":
            LawyerVerificationService.approve(verification)
            return Response({"message": "Lawyer verified successfully"}, status=200)

        if action == "reject":
            reason = request.data.get("reason")
            LawyerVerificationService.reject(verification, reason)
            return Response({"message": "Lawyer verification rejected"}, status=200)

        return Response({"error": "Invalid action"}, status=400)


# -------------------------
# LIST & DETAIL
# -------------------------
class LawyerListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(tags=["lawyers"])
    def get(self, request):
        admin = is_admin_user(request.user)

        qs = Lawyer.objects.select_related(
            "user",
            "user__bar_verification"
        ).prefetch_related("services")

        if not admin:
            qs = qs.filter(
                user__bar_verification__status=VerificationStatus.VERIFIED
            )
            serializer_class = LawyerPublicSerializer
        else:
            serializer_class = LawyerAdminSerializer

        data = [
            {
                "user": lawyer.user,
                "profile": lawyer,
                "verification": getattr(lawyer.user, "bar_verification", None),
            }
            for lawyer in qs
        ]

        serializer = serializer_class(data, many=True)
        return Response(serializer.data)


class LawyerDetailView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(tags=["lawyers"])
    def get(self, request, lawyer_id):
        admin = is_admin_user(request.user)

        qs = Lawyer.objects.select_related(
            "user",
            "user__bar_verification"
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
