from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema

from accounts.permissions import IsFirmVerified
from firms.api.serializers import FirmMemberSerializer


class FirmMembersListView(APIView):
    permission_classes = [IsAuthenticated, IsFirmVerified]

    @extend_schema(
        summary="List firm members",
        responses={200: FirmMemberSerializer(many=True)},
        tags=["firm-members"],
    )
    def get(self, request):
        firm = request.user.firm_profile
        members = firm.members.select_related(
            "lawyer",
            "lawyer__user",
        )

        serializer = FirmMemberSerializer(members, many=True)
        return Response(serializer.data)
