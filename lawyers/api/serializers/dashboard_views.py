from datetime import timedelta
from dateutil.relativedelta import relativedelta

from django.utils import timezone
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema

from accounts.permissions import IsLawyerUser
from base.constants.case import CaseStatus
from base.constants.booking_status import BookingStatus
from base.constants.user_roles import UserRoles

from lawyers.models import Lawyer
from cases.models import Case
from bookings.models import Booking
from lawyers.api.serializers.lawyer_serializers import LawyerDashboardSerializer


class LawyerDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated, IsLawyerUser]

    @extend_schema(
        summary="Lawyer Dashboard",
        description="Returns dashboard statistics for authenticated lawyer.",
        responses={200: LawyerDashboardSerializer},
        tags=["lawyers"],
    )
    def get(self, request):

        lawyer = Lawyer.objects.get(user=request.user)

        # ------------------------------------
        # Total Cases (Owned + Assigned)
        # ------------------------------------
        case_qs = Case.objects.filter(
            Q(owner_lawyer=lawyer) |
            Q(assigned_lawyers__lawyer=lawyer)
        ).distinct()

        total_cases = case_qs.count()

        # ------------------------------------
        # Total Ongoing Cases
        # ------------------------------------
        total_ongoing_cases = case_qs.filter(
            status=CaseStatus.ONGOING
        ).count()

        # ------------------------------------
        # Pending Bookings
        # ------------------------------------
        total_pending_bookings = Booking.objects.filter(
            created_to=request.user,
            status=BookingStatus.PENDING
        ).count()

        # ------------------------------------
        # Cases per Month (Last 12 Months)
        # ------------------------------------
        now = timezone.now()
        start_date = now - relativedelta(months=11)

        monthly_data = (
            case_qs.filter(created_at__gte=start_date)
            .annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(count=Count("id"))
            .order_by("month")
        )

        # Convert to dict for easier lookup
        month_map = {
            item["month"].strftime("%Y-%m"): item["count"]
            for item in monthly_data
        }

        # Build full 12 months structure
        cases_per_month = []
        for i in range(12):
            month_date = start_date + relativedelta(months=i)
            key = month_date.strftime("%Y-%m")
            cases_per_month.append({
                "month": month_date.strftime("%b"),  # Jan, Feb, etc
                "year": month_date.year,
                "count": month_map.get(key, 0)
            })

        data = {
            "total_cases": total_cases,
            "total_ongoing_cases": total_ongoing_cases,
            "total_pending_bookings": total_pending_bookings,
            "cases_per_month": cases_per_month,
        }

        return Response(LawyerDashboardSerializer(data).data)
