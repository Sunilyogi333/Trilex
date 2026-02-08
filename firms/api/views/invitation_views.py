from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema, OpenApiResponse
from base.pagination import DefaultPageNumberPagination
from base.openapi import PAGE_PARAMETER, PAGE_SIZE_PARAMETER

from accounts.permissions import IsFirmVerified
from firms.services.firm_invitation_service import FirmInvitationService
from firms.api.serializers import (
    FirmInvitationSerializer,
    FirmSentInvitationListSerializer,
)
from lawyers.models import Lawyer


class FirmInviteLawyerView(APIView):
    permission_classes = [IsAuthenticated, IsFirmVerified]

    @extend_schema(
        summary="Invite lawyer to firm",
        request=None,
        responses={
            201: FirmInvitationSerializer,
            400: OpenApiResponse(description="Invalid request"),
        },
        tags=["firm-invitations"],
    )
    def post(self, request, lawyer_id):
        firm = request.user.firm_profile
        lawyer = get_object_or_404(Lawyer, id=lawyer_id)

        try:
            invitation = FirmInvitationService.invite_lawyer(
                firm=firm,
                lawyer=lawyer
            )
        except ValidationError as e:
            return Response({"error": e.message}, status=400)

        serializer = FirmInvitationSerializer(invitation)
        return Response(serializer.data, status=201)



class FirmSentInvitationsView(APIView):
    permission_classes = [IsAuthenticated, IsFirmVerified]

    @extend_schema(
        summary="List firm sent invitations",
        parameters=[
            PAGE_PARAMETER,
            PAGE_SIZE_PARAMETER,
        ],
        responses={200: FirmSentInvitationListSerializer(many=True)},
        tags=["firm-invitations"],
    )
    def get(self, request):
        firm = request.user.firm_profile

        qs = firm.sent_invitations.select_related(
            "lawyer",
            "lawyer__user",
        )

        paginator = DefaultPageNumberPagination()
        page = paginator.paginate_queryset(qs, request)

        serializer = FirmSentInvitationListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)