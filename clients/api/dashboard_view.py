from django.db.models import Q

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema

from accounts.permissions import IsClientUser
from base.constants.case import CaseStatus
from base.constants.booking_status import BookingStatus
from base.constants.verification import VerificationStatus

from bookings.models import Booking
from cases.models import Case
from clients.models import IDVerification
from clients.api.serializers import ClientDashboardSerializer


class ClientDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated, IsClientUser]

    @extend_schema(
        summary="Client Dashboard",
        description="Returns dashboard statistics for authenticated client.",
        responses={200: ClientDashboardSerializer},
        tags=["clients"],
    )
    def get(self, request):

        user = request.user
        client_profile = user.client_profile

        # Accepted Bookings
        accepted_bookings = Booking.objects.filter(
            created_by=user,
            status=BookingStatus.ACCEPTED
        ).count()

        # Active Cases (Not completed)
        active_cases = Case.objects.filter(
            client=client_profile,
            status__in=[
                CaseStatus.DRAFT,
                CaseStatus.REGISTERED,
                CaseStatus.ONGOING,
            ]
        ).count()

        # Verification Status
        verification = IDVerification.objects.filter(
            user=user
        ).first()

        if not verification:
            verification_status = VerificationStatus.NOT_SUBMITTED
        else:
            verification_status = verification.status

        data = {
            "accepted_bookings": accepted_bookings,
            "active_cases": active_cases,
            "verification_status": verification_status,
        }

        return Response(ClientDashboardSerializer(data).data)
