from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter

from base.constants.user_roles import UserRoles
from base.constants.verification import VerificationStatus
from accounts.permissions import IsFirmUser, IsAdminUser

from firms.models import FirmVerification
from firms.api.serializers import (
    FirmVerificationSerializer,
    FirmVerificationMeSerializer,
    FirmRejectReasonSerializer,
    FirmAdminVerificationSerializer

)
from firms.services.firm_profile_service import FirmProfileService
from firms.services.verification_service import FirmVerificationService
from addresses.services.address_service import AddressService
from base.pagination import DefaultPageNumberPagination

User = get_user_model()


def is_admin_user(user):
    return user.is_authenticated and user.role == UserRoles.ADMIN

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