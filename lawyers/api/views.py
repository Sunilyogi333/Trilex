# lawyers/api/views.py

from django.db import transaction
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from drf_spectacular.utils import extend_schema

from accounts.constants import UserRoles
from accounts.permissions import IsLawyerUser, IsAdminUser
from accounts.services.auth_service import AuthService

from lawyers.models import Lawyer, BarVerification
from lawyers.api.serializers import (
    LawyerSignupSerializer,
    BarVerificationSerializer,
    BarVerificationMeSerializer
)
from lawyers.services.verification_service import LawyerVerificationService

User = get_user_model()


# -------------------------
# SIGNUP
# -------------------------

class LawyerSignupView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=LawyerSignupSerializer,
        responses={201: dict},
        tags=["lawyers"]
    )
    @transaction.atomic
    def post(self, request):
        serializer = LawyerSignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        verification_data = data.pop("verification")

        if User.objects.filter(email=data["email"]).exists():
            return Response(
                {"error": "Email already registered"},
                status=400
            )

        # 1️⃣ Create User
        user = User.objects.create_user(
            email=data["email"],
            password=data["password"],
            role=UserRoles.LAWYER,
            is_email_verified=False,
        )

        # 2️⃣ Create Lawyer profile
        Lawyer.objects.create(user=user)

        # 3️⃣ Create Bar Verification (PENDING)
        BarVerification.objects.create(
            user=user,
            status=BarVerification.Status.PENDING,
            **verification_data
        )

        # 4️⃣ Send email verification
        AuthService.send_signup_verification(
            user=user,
            client_type=data["client_type"]
        )

        return Response(
            {
                "message": "Lawyer signup successful. Verification submitted.",
                "verification_status": BarVerification.Status.PENDING,
            },
            status=201
        )


# -------------------------
# LAWYER: SUBMIT / RESUBMIT BAR VERIFICATION
# -------------------------
class BarVerificationView(APIView):
    permission_classes = [IsAuthenticated, IsLawyerUser]

    @extend_schema(
        request=BarVerificationSerializer,
        responses={201: dict},
        tags=["lawyers"]
    )
    def post(self, request):
        serializer = BarVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        verification = LawyerVerificationService.submit(
            user=request.user,
            **serializer.validated_data
        )

        return Response(
            {
                "message": "Bar verification submitted",
                "status": verification.status,
            },
            status=201
        )


# -------------------------
# LAWYER: VIEW OWN STATUS
# -------------------------
class BarVerificationMeView(APIView):
    permission_classes = [IsAuthenticated, IsLawyerUser]

    @extend_schema(
        tags=["lawyers"]
    )

    def get(self, request):
        verification = BarVerification.objects.filter(
            user=request.user
        ).first()

        if not verification:
            return Response(
                {"status": BarVerification.Status.NOT_SUBMITTED},
                status=200
            )

        serializer = BarVerificationMeSerializer(verification)
        return Response(serializer.data, status=200)


# -------------------------
# ADMIN: LIST / ACTIONS
# -------------------------
class BarVerificationListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    @extend_schema(
        tags=["lawyers"]
    )

    def get(self, request):
        qs = BarVerification.objects.all()
        status = request.query_params.get("status")

        if status:
            qs = qs.filter(status=status)

        return Response(
            [
                {
                    "id": v.id,
                    "email": v.user.email,
                    "full_name": v.full_name,
                    "status": v.status,
                }
                for v in qs
            ],
            status=200
        )


class BarVerificationActionView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    @extend_schema(
        tags=["lawyers"]
    )

    def post(self, request, verification_id, action):
        verification = get_object_or_404(
            BarVerification,
            id=verification_id
        )

        if action == "approve":
            LawyerVerificationService.approve(verification)
            return Response({"message": "Lawyer verified"}, status=200)

        if action == "reject":
            LawyerVerificationService.reject(
                verification,
                request.data.get("reason")
            )
            return Response({"message": "Lawyer rejected"}, status=200)

        return Response({"error": "Invalid action"}, status=400)
