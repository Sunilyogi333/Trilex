from dateutil.relativedelta import relativedelta
from django.utils import timezone
from django.db.models import Count
from django.db.models.functions import TruncMonth

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema

from accounts.permissions import IsFirmUser
from base.constants.case import CaseStatus
from base.constants.booking_status import BookingStatus

from firms.models import Firm
from cases.models import Case
from bookings.models import Booking
from firms.api.serializers.dashboard import FirmDashboardSerializer


class FirmDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated, IsFirmUser]

    @extend_schema(
        summary="Firm Dashboard",
        description="Returns dashboard statistics for authenticated firm.",
        responses={200: FirmDashboardSerializer},
        tags=["firms"],
    )
    def get(self, request):

        firm = request.user.firm_profile

        # -----------------------------------
        # 1️⃣ Total Cases (Firm-owned only)
        # -----------------------------------
        case_qs = Case.objects.filter(
            owner_firm=firm
        )

        total_cases = case_qs.count()

        # -----------------------------------
        # 2️⃣ Ongoing Cases
        # -----------------------------------
        total_ongoing_cases = case_qs.filter(
            status=CaseStatus.ONGOING
        ).count()

        # -----------------------------------
        # 3️⃣ Pending Bookings
        # -----------------------------------
        total_pending_bookings = Booking.objects.filter(
            created_to=request.user,
            status=BookingStatus.PENDING
        ).count()

        # -----------------------------------
        # 4️⃣ Total Firm Members
        # -----------------------------------
        total_members = firm.members.count()

        # -----------------------------------
        # 5️⃣ Cases Per Month (Last 12 Months)
        # -----------------------------------
        now = timezone.now()
        start_date = now - relativedelta(months=11)

        monthly_data = (
            case_qs.filter(created_at__gte=start_date)
            .annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(count=Count("id"))
            .order_by("month")
        )

        month_map = {
            item["month"].strftime("%Y-%m"): item["count"]
            for item in monthly_data
        }

        cases_per_month = []
        for i in range(12):
            month_date = start_date + relativedelta(months=i)
            key = month_date.strftime("%Y-%m")

            cases_per_month.append({
                "month": month_date.strftime("%b"),
                "year": month_date.year,
                "count": month_map.get(key, 0),
            })

        data = {
            "total_cases": total_cases,
            "total_ongoing_cases": total_ongoing_cases,
            "total_pending_bookings": total_pending_bookings,
            "total_members": total_members,
            "cases_per_month": cases_per_month,
        }

        return Response(FirmDashboardSerializer(data).data)
