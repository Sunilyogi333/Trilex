# firms/api/views.py

from django.db import transaction
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from drf_spectacular.utils import extend_schema

from accounts.constants import UserRoles
from accounts.permissions import IsFirmUser, IsAdminUser
from accounts.services.auth_service import AuthService

from firms.models import Firm, FirmVerification
from firms.api.serializers import (
    FirmSignupSerializer,
    FirmVerificationSerializer,
    FirmVerificationMeSerializer
)
from firms.services.verification_service import FirmVerificationService

User = get_user_model()


# -------------------------
# SIGNUP
# -------------------------
class FirmSignupView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=FirmSignupSerializer,
        responses={201: dict},
        tags=["firms"]
    )
    @transaction.atomic
    def post(self, request):
        serializer = FirmSignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        verification_data = data.pop("verification")

        if User.objects.filter(email=data["email"]).exists():
            return Response(
                {"error": "Email already registered"},
                status=400
            )

        user = User.objects.create_user(
            email=data["email"],
            password=data["password"],
            role=UserRoles.FIRM,
            is_email_verified=False,
        )

        Firm.objects.create(user=user)

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
            {
                "message": "Firm signup successful. Verification submitted.",
                "verification_status": FirmVerification.Status.PENDING,
            },
            status=201
        )

# -------------------------
# FIRM: SUBMIT / RESUBMIT VERIFICATION
# -------------------------
class FirmVerificationView(APIView):
    permission_classes = [IsAuthenticated, IsFirmUser]

    @extend_schema(
        request=FirmVerificationSerializer,
        responses={201: dict},
        tags=["firms"]
    )
    def post(self, request):
        serializer = FirmVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        verification = FirmVerificationService.submit(
            user=request.user,
            **serializer.validated_data
        )

        return Response(
            {
                "message": "Firm verification submitted",
                "status": verification.status,
            },
            status=201
        )


# -------------------------
# FIRM: VIEW OWN STATUS
# -------------------------
class FirmVerificationMeView(APIView):
    permission_classes = [IsAuthenticated, IsFirmUser]

    @extend_schema(
        tags=["firms"]
    )

    def get(self, request):
        verification = FirmVerification.objects.filter(
            user=request.user
        ).first()

        if not verification:
            return Response(
                {"status": FirmVerification.Status.NOT_SUBMITTED},
                status=200
            )

        serializer = FirmVerificationMeSerializer(verification)
        return Response(serializer.data, status=200)


# -------------------------
# ADMIN: LIST / ACTIONS
# -------------------------
class FirmVerificationListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    @extend_schema(
        tags=["firms"]
    )

    def get(self, request):
        qs = FirmVerification.objects.all()
        status = request.query_params.get("status")

        if status:
            qs = qs.filter(status=status)

        return Response(
            [
                {
                    "id": v.id,
                    "email": v.user.email,
                    "firm_name": v.firm_name,
                    "status": v.status,
                }
                for v in qs
            ],
            status=200
        )


class FirmVerificationActionView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    @extend_schema(
        tags=["firms"]
    )

    def post(self, request, verification_id, action):
        verification = get_object_or_404(
            FirmVerification,
            id=verification_id
        )

        if action == "approve":
            FirmVerificationService.approve(verification)
            return Response({"message": "Firm verified"}, status=200)

        if action == "reject":
            FirmVerificationService.reject(
                verification,
                request.data.get("reason")
            )
            return Response({"message": "Firm rejected"}, status=200)

        return Response({"error": "Invalid action"}, status=400)
