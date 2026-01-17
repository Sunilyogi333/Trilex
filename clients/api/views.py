from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import IsClientUser
from clients.api.serializers import (
    ClientIDVerificationSerializer,
    ClientIDVerificationMeSerializer
)
from clients.services.client_verification_service import ClientVerificationService

class ClientIDVerificationView(APIView):
    permission_classes = [IsAuthenticated, IsClientUser]

    def post(self, request):
        serializer = ClientIDVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        verification = ClientVerificationService.create_verification(
            user=request.user,
            **serializer.validated_data
        )

        return Response(
            {
                "message": "ID verification submitted successfully",
                "status": verification.status,
            },
            status=201
        )

    def patch(self, request):
        serializer = ClientIDVerificationSerializer(
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)

        verification = ClientVerificationService.update_verification(
            user=request.user,
            **serializer.validated_data
        )

        return Response(
            {
                "message": "ID verification updated and resubmitted",
                "status": verification.status,
            },
            status=200
        )


class ClientIDVerificationMeView(APIView):
    permission_classes = [IsAuthenticated, IsClientUser]

    def get(self, request):
        verification = getattr(request.user, "client_verification", None)

        if not verification:
            return Response(
                {"status": "NOT_SUBMITTED"},
                status=200
            )

        serializer = ClientIDVerificationMeSerializer(verification)
        return Response(serializer.data, status=200)


