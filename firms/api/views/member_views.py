from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema
from base.pagination import DefaultPageNumberPagination
from base.openapi import PAGE_PARAMETER, PAGE_SIZE_PARAMETER

from accounts.permissions import IsFirmVerified
from firms.api.serializers import FirmMemberSerializer


class FirmMembersListView(APIView):
    permission_classes = [IsAuthenticated, IsFirmVerified]

    @extend_schema(
        summary="List firm members",
        parameters=[
            PAGE_PARAMETER,
            PAGE_SIZE_PARAMETER,
        ],
        responses={200: FirmMemberSerializer(many=True)},
        tags=["firm-members"],
    )
    def get(self, request):
        firm = request.user.firm_profile

        qs = firm.members.select_related(
            "lawyer",
            "lawyer__user",
        )

        paginator = DefaultPageNumberPagination()
        page = paginator.paginate_queryset(qs, request)

        serializer = FirmMemberSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


