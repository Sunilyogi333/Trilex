from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiResponse,
)
from base.pagination import DefaultPageNumberPagination
from base.openapi import PAGE_PARAMETER, PAGE_SIZE_PARAMETER

from accounts.permissions import IsLawyerVerified
from firms.models import FirmInvitation
from firms.services.firm_invitation_service import FirmInvitationService
from firms.api.serializers import LawyerReceivedInvitationListSerializer


class LawyerInvitationsListView(APIView):
    permission_classes = [IsAuthenticated, IsLawyerVerified]

    @extend_schema(
        summary="List received firm invitations",
        parameters=[
            PAGE_PARAMETER,
            PAGE_SIZE_PARAMETER,
        ],
        responses={200: LawyerReceivedInvitationListSerializer(many=True)},
        tags=["lawyer-invitations"],
    )
    def get(self, request):
        lawyer = request.user.lawyer_profile

        qs = lawyer.received_invitations.select_related(
            "firm",
            "firm__user",
        )

        paginator = DefaultPageNumberPagination()
        page = paginator.paginate_queryset(qs, request)

        serializer = LawyerReceivedInvitationListSerializer(
            page,
            many=True
        )
        return paginator.get_paginated_response(serializer.data)

class LawyerInvitationRespondView(APIView):
    permission_classes = [IsAuthenticated, IsLawyerVerified]

    @extend_schema(
        summary="Accept or reject firm invitation",
        parameters=[
            OpenApiParameter(
                name="action",
                type=str,
                enum=["accept", "reject"],
                location=OpenApiParameter.PATH,
            )
        ],
        responses={200: OpenApiResponse(description="Action completed")},
        tags=["lawyer-invitations"],
    )
    def post(self, request, invitation_id, action):
        lawyer = request.user.lawyer_profile

        invitation = get_object_or_404(
            FirmInvitation,
            id=invitation_id,
            lawyer=lawyer,
        )

        try:
            if action == "accept":
                FirmInvitationService.accept_invitation(
                    invitation=invitation
                )
                return Response(
                    {"message": "Invitation accepted"},
                    status=200
                )

            if action == "reject":
                FirmInvitationService.reject_invitation(
                    invitation=invitation
                )
                return Response(
                    {"message": "Invitation rejected"},
                    status=200
                )

        except ValidationError as e:
            return Response({"error": e.message}, status=400)

        return Response({"error": "Invalid action"}, status=400)
