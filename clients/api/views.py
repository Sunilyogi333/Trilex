from django.db import transaction
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from drf_spectacular.utils import extend_schema

from base.constants.user_roles import UserRoles
from base.constants.verification import VerificationStatus
from accounts.permissions import IsClientUser, IsAdminUser
from accounts.services.auth_service import AuthService

from clients.models import Client, IDVerification
from clients.services.verification_service import ClientVerificationService
from clients.services.client_profile_service import ClientProfileService
from clients.api.serializers import (
    ClientSignupSerializer,
    ClientMeSerializer,
    ClientProfileUpdateSerializer,
    IDVerificationSerializer,
    IDVerificationMeSerializer,
    ClientPublicSerializer,
    ClientAdminSerializer,
    ClientAdminVerificationSerializer
)

User = get_user_model()


def is_admin_user(user):
    return user.is_authenticated and user.role == UserRoles.ADMIN


# -------------------------
# SIGNUP
# -------------------------
class ClientSignupView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(request=ClientSignupSerializer, responses={201: dict}, tags=["clients"])
    @transaction.atomic
    def post(self, request):
        serializer = ClientSignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if User.objects.filter(email=serializer.validated_data["email"]).exists():
            return Response({"error": "Email already registered"}, status=400)

        user = User.objects.create_user(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
            role=UserRoles.CLIENT,
            is_email_verified=False,
        )

        Client.objects.create(user=user)

        AuthService.send_signup_verification(
            user=user,
            client_type=serializer.validated_data["client_type"],
        )

        return Response(
            {"message": "Client signup successful. Please verify your email."},
            status=201,
        )


# -------------------------
# ME
# -------------------------
class ClientMeView(APIView):
    permission_classes = [IsAuthenticated, IsClientUser]

    @extend_schema(responses={200: ClientMeSerializer}, tags=["clients"])
    def get(self, request):
        client = request.user.client_profile
        verification = IDVerification.objects.filter(user=request.user).first()

        serializer = ClientMeSerializer({
            "user": request.user,
            "profile": client,
            "verification": verification,
        })
        return Response(serializer.data)


class ClientProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated, IsClientUser]

    @extend_schema(request=ClientProfileUpdateSerializer, responses={200: dict}, tags=["clients"])
    def patch(self, request):
        client = request.user.client_profile

        serializer = ClientProfileUpdateSerializer(
            client, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)

        ClientProfileService.update_profile(client, serializer.validated_data)

        return Response({"message": "Profile updated successfully"})


# -------------------------
# VERIFICATION
# -------------------------
class IDVerificationView(APIView):
    permission_classes = [IsAuthenticated, IsClientUser]

    @extend_schema(request=IDVerificationSerializer, responses={201: dict}, tags=["clients"])
    def post(self, request):
        serializer = IDVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        verification = ClientVerificationService.submit(
            user=request.user,
            **serializer.validated_data
        )

        return Response(
            {"message": "ID verification submitted", "status": verification.status},
            status=201,
        )


class IDVerificationMeView(APIView):
    permission_classes = [IsAuthenticated, IsClientUser]

    @extend_schema(responses=IDVerificationMeSerializer, tags=["clients"])
    def get(self, request):
        verification = IDVerification.objects.filter(user=request.user).first()
        if not verification:
            return Response({"status": IDVerification.Status.NOT_SUBMITTED})

        serializer = IDVerificationMeSerializer(verification)
        return Response(serializer.data)

# -------------------------
# ADMIN: LIST VERIFICATIONS
# -------------------------
class IDVerificationListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    @extend_schema(
        responses={200: ClientAdminVerificationSerializer(many=True)},
        tags=["clients"]
    )
    def get(self, request):
        qs = IDVerification.objects.select_related("user")

        status = request.query_params.get("status")
        if status:
            qs = qs.filter(status=status)

        serializer = ClientAdminVerificationSerializer(qs, many=True)
        return Response(serializer.data, status=200)


# -------------------------
# ADMIN: APPROVE / REJECT
# -------------------------
class IDVerificationActionView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    @extend_schema(tags=["clients"])
    def post(self, request, verification_id, action):
        verification = get_object_or_404(IDVerification, id=verification_id)

        if action == "approve":
            ClientVerificationService.approve(verification)
            return Response({"message": "Client verified successfully"})

        if action == "reject":
            ClientVerificationService.reject(
                verification, request.data.get("reason")
            )
            return Response({"message": "Client verification rejected"})

        return Response({"error": "Invalid action"}, status=400)


# -------------------------
# LIST & DETAIL
# -------------------------
class ClientListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(tags=["clients"])
    def get(self, request):
        admin = is_admin_user(request.user)

        qs = Client.objects.select_related("user")

        if not admin:
            qs = qs.filter(
                user__client_verification__status=VerificationStatus.VERIFIED
            )
            serializer_class = ClientPublicSerializer
        else:
            serializer_class = ClientAdminSerializer

        data = [
            {
                "user": client.user,
                "profile": client,
                "verification": IDVerification.objects.filter(
                    user=client.user
                ).first(),
            }
            for client in qs
        ]

        serializer = serializer_class(data, many=True)
        return Response(serializer.data)


class ClientDetailView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(tags=["clients"])
    def get(self, request, client_id):
        admin = is_admin_user(request.user)

        qs = Client.objects.select_related("user")

        if not admin:
            client = get_object_or_404(
                qs,
                id=client_id,
                user__client_verification__status=VerificationStatus.VERIFIED,
            )
            serializer_class = ClientPublicSerializer
        else:
            client = get_object_or_404(qs, id=client_id)
            serializer_class = ClientAdminSerializer

        verification = IDVerification.objects.filter(user=client.user).first()

        serializer = serializer_class({
            "user": client.user,
            "profile": client,
            "verification": verification,
        })
        return Response(serializer.data)
