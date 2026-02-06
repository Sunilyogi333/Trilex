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
from base.constants.user_roles import UserRoles
from accounts.permissions import IsAuthenticatedUser, IsEmailVerified, IsClientUser, IsClientVerified, IsVerifiedLawyerOrFirm
from drf_spectacular.utils import extend_schema, OpenApiResponse
from drf_spectacular.utils import extend_schema_field



class BookingCreateAPIView(APIView):
    permission_classes = [
        IsAuthenticatedUser,
        IsEmailVerified,
        IsClientUser,
        IsClientVerified,
    ]

    @extend_schema(
        summary="Create booking",
        description="Client creates a booking request to a lawyer or firm.",
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
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        booking = BookingService.create_booking(
            created_by=request.user,
            **serializer.validated_data
        )

        return Response(
            BookingDetailSerializer(booking).data,
            status=status.HTTP_201_CREATED
        )

class MySentBookingsAPIView(APIView):
    permission_classes = [  
        IsAuthenticatedUser,
        IsEmailVerified,
        IsClientUser,
        IsClientVerified,
    ]

    @extend_schema(
        summary="My sent bookings",
        description="List bookings created by the authenticated client.",
        responses={200: BookingListSerializer(many=True)},
        tags=["bookings"],
    )
    def get(self, request):
        bookings = Booking.objects.filter(
            created_by=request.user
        )

        serializer = BookingListSerializer(bookings, many=True)
        return Response(serializer.data)

class MyReceivedBookingsAPIView(APIView):
    permission_classes = [
        IsAuthenticatedUser,
        IsEmailVerified,
        IsVerifiedLawyerOrFirm,
    ]

    @extend_schema(
        summary="My received bookings",
        description="List booking requests received by verified lawyer or firm.",
        responses={200: BookingListSerializer(many=True)},
        tags=["bookings"],
    )
    def get(self, request):
        bookings = Booking.objects.filter(
            created_to=request.user
        )

        serializer = BookingListSerializer(bookings, many=True)
        return Response(serializer.data)

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

        if request.user not in [booking.created_by, booking.created_to]:
            return Response(
                {"detail": "You do not have access to this booking."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = BookingDetailSerializer(booking)
        return Response(serializer.data)

class BookingAcceptAPIView(APIView):
    permission_classes = [
        IsAuthenticatedUser,
        IsEmailVerified,
        IsVerifiedLawyerOrFirm,
    ]
    @extend_schema(
        summary="Accept booking",
        description="Lawyer or firm accepts a booking request.",
        responses={200: BookingDetailSerializer},
        tags=["bookings"],
    )
    def post(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk)

        booking = BookingService.accept_booking(
            booking=booking,
            user=request.user
        )

        return Response(
            BookingDetailSerializer(booking).data
        )

class BookingRejectAPIView(APIView):
    permission_classes = [
        IsAuthenticatedUser,
        IsEmailVerified,
        IsVerifiedLawyerOrFirm,
    ]
    @extend_schema(
        summary="Reject booking",
        description="Lawyer or firm rejects a booking request.",
        responses={200: BookingDetailSerializer},
        tags=["bookings"],
    )
    def post(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk)

        booking = BookingService.reject_booking(
            booking=booking,
            user=request.user
        )

        return Response(
            BookingDetailSerializer(booking).data
        )
