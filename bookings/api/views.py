from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from bookings.models import Booking
from bookings.api.serializers import (
    BookingCreateSerializer,
    BookingListSerializer,
    BookingDetailSerializer,
)
from bookings.services.services import BookingService
from accounts.permissions import (
    IsAuthenticatedUser,
    IsEmailVerified,
    IsClientUser,
    IsClientVerified,
    IsVerifiedLawyerOrFirm,
)
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from base.constants.booking_status import BookingStatus
from base.pagination import DefaultPageNumberPagination
from rest_framework.exceptions import APIException

# -------------------------
# CREATE BOOKING (CLIENT)
# -------------------------
class BookingCreateAPIView(APIView):
    permission_classes = [
        IsAuthenticatedUser,
        IsEmailVerified,
        IsClientUser,
        IsClientVerified,
    ]

    @extend_schema(
        summary="Create booking",
        description="Verified client creates a booking request to a lawyer or firm.",
        request=BookingCreateSerializer,
        responses={
            201: BookingDetailSerializer,
            400: OpenApiResponse(description="Validation error"),
            403: OpenApiResponse(description="Forbidden"),
        },
        tags=["bookings"],
    )
    def post(self, request):
        serializer = BookingCreateSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)

        booking = BookingService.create_booking(
            created_by=request.user,
            **serializer.validated_data,
        )

        return Response(
            BookingDetailSerializer(booking).data,
            status=status.HTTP_201_CREATED,
        )


# -------------------------
# MY SENT BOOKINGS (CLIENT)
# -------------------------
class MySentBookingsAPIView(APIView):
    permission_classes = [
        IsAuthenticatedUser,
        IsEmailVerified,
        IsClientUser,
        IsClientVerified,
    ]

    @extend_schema(
        summary="My sent bookings",
        description="List bookings created by the authenticated client. Can be filtered by status.",
        parameters=[
            OpenApiParameter(
                name="status",
                type=str,
                location=OpenApiParameter.QUERY,
                enum=[s for s, _ in BookingStatus.choices],
                description="Filter bookings by status",
            ),
            OpenApiParameter("page", int, OpenApiParameter.QUERY),
            OpenApiParameter("page_size", int, OpenApiParameter.QUERY),
        ],
        responses={200: BookingListSerializer(many=True)},
        tags=["bookings"],
    )
    def get(self, request):
        qs = Booking.objects.filter(created_by=request.user)

        status_param = request.query_params.get("status")
        if status_param:
            valid_statuses = {s for s, _ in BookingStatus.choices}
            if status_param not in valid_statuses:
                raise APIException("Invalid booking status.")
            qs = qs.filter(status=status_param)

        paginator = DefaultPageNumberPagination()
        page = paginator.paginate_queryset(qs, request)

        serializer = BookingListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

# -------------------------
# MY RECEIVED BOOKINGS (LAWYER / FIRM)
# -------------------------
class MyReceivedBookingsAPIView(APIView):
    permission_classes = [
        IsAuthenticatedUser,
        IsEmailVerified,
        IsVerifiedLawyerOrFirm,
    ]

    @extend_schema(
        summary="My received bookings",
        description="List booking requests received by verified lawyer or firm. Can be filtered by status.",
        parameters=[
            OpenApiParameter(
                name="status",
                type=str,
                location=OpenApiParameter.QUERY,
                enum=[s for s, _ in BookingStatus.choices],
                description="Filter bookings by status",
            ),
            OpenApiParameter("page", int, OpenApiParameter.QUERY),
            OpenApiParameter("page_size", int, OpenApiParameter.QUERY),
        ],
        responses={200: BookingListSerializer(many=True)},
        tags=["bookings"],
    )
    def get(self, request):
        qs = Booking.objects.filter(created_to=request.user)

        status_param = request.query_params.get("status")
        if status_param:
            valid_statuses = {s for s, _ in BookingStatus.choices}
            if status_param not in valid_statuses:
                raise APIException("Invalid booking status.")
            qs = qs.filter(status=status_param)

        paginator = DefaultPageNumberPagination()
        page = paginator.paginate_queryset(qs, request)

        serializer = BookingListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


# -------------------------
# BOOKING DETAIL (BOTH SIDES)
# -------------------------
class BookingDetailAPIView(APIView):
    permission_classes = [IsAuthenticatedUser]

    @extend_schema(
        summary="Booking detail",
        description="Retrieve booking details (client or receiver only).",
        responses={200: BookingDetailSerializer},
        tags=["bookings"],
    )
    def get(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk)

        if request.user not in (booking.created_by, booking.created_to):
            return Response(
                {"detail": "You do not have access to this booking."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = BookingDetailSerializer(booking)
        return Response(serializer.data)


# -------------------------
# ACCEPT BOOKING
# -------------------------
class BookingAcceptAPIView(APIView):
    permission_classes = [
        IsAuthenticatedUser,
        IsEmailVerified,
        IsVerifiedLawyerOrFirm,
    ]

    @extend_schema(
        summary="Accept booking",
        description="Lawyer or firm accepts a booking request.",
        request=None,
        responses={200: BookingDetailSerializer},
        tags=["bookings"],
    )
    def post(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk)

        booking = BookingService.accept_booking(
            booking=booking,
            user=request.user,
        )

        return Response(BookingDetailSerializer(booking).data)


# -------------------------
# REJECT BOOKING
# -------------------------
class BookingRejectAPIView(APIView):
    permission_classes = [
        IsAuthenticatedUser,
        IsEmailVerified,
        IsVerifiedLawyerOrFirm,
    ]

    @extend_schema(
        summary="Reject booking",
        description="Lawyer or firm rejects a booking request.",
        request=None,
        responses={200: BookingDetailSerializer},
        tags=["bookings"],
    )
    def post(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk)

        booking = BookingService.reject_booking(
            booking=booking,
            user=request.user,
        )

        return Response(BookingDetailSerializer(booking).data)
