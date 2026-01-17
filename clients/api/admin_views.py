from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from accounts.permissions import IsAdminUser
from clients.models import ClientIDVerification
from clients.services.client_verification_service import ClientVerificationService

class AdminClientVerificationListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        status = request.query_params.get("status")
        qs = ClientIDVerification.objects.all()

        if status:
            qs = qs.filter(status=status)

        data = [
            {
                "id": v.id,
                "email": v.user.email,
                "full_name": v.full_name,
                "status": v.status,
            }
            for v in qs
        ]

        return Response(data, status=200)


class AdminClientVerificationActionView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, verification_id, action):
        verification = get_object_or_404(
            ClientIDVerification,
            id=verification_id
        )

        if verification.status == ClientIDVerification.Status.VERIFIED:
            return Response(
                {"error": "Verification already approved"},
                status=400
            )

        if action == "approve":
            ClientVerificationService.approve(verification)
            return Response({"message": "Client verified"}, status=200)

        if action == "reject":
            reason = request.data.get("reason")
            if not reason:
                return Response(
                    {"error": "Rejection reason required"},
                    status=400
                )

            ClientVerificationService.reject(verification, reason)
            return Response({"message": "Client rejected"}, status=200)

        return Response({"error": "Invalid action"}, status=400)
