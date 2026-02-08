from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
    OpenApiParameter,
)

from base.constants.user_roles import UserRoles
from base.constants.verification import VerificationStatus
from accounts.permissions import IsLawyerUser, IsAdminUser

from lawyers.models import BarVerification
from lawyers.services.verification_service import LawyerVerificationService

from lawyers.api.serializers import (
    BarVerificationSerializer,
    BarVerificationMeSerializer,
    LawyerRejectReasonSerializer,
    LawyerAdminVerificationSerializer,
)
from base.pagination import DefaultPageNumberPagination

User = get_user_model()


def is_admin_user(user):
    return user.is_authenticated and user.role == UserRoles.ADMIN

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
        existing = BarVerification.objects.filter(user=request.user).first()
    
        serializer = BarVerificationSerializer(
            instance=existing,
            data=request.data
        )
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