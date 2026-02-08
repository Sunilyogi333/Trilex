from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

from accounts.permissions import IsLawyerVerified
from firms.models import FirmInvitation
from firms.services.firm_invitation_service import FirmInvitationService
from firms.api.serializers import FirmInvitationListSerializer


class LawyerInvitationsListView(APIView):
    permission_classes = [IsAuthenticated, IsLawyerVerified]

    @extend_schema(
        summary="List received firm invitations",
        responses={200: FirmInvitationListSerializer(many=True)},
        tags=["lawyer-invitations"],
    )
    def get(self, request):
        lawyer = request.user.lawyer_profile

        invitations = lawyer.received_invitations.select_related(
            "firm",
            "firm__user",
        )

        serializer = FirmInvitationListSerializer(
            invitations,
            many=True
        )
        return Response(serializer.data)


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
