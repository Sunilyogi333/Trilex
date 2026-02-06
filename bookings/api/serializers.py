from rest_framework import serializers
from django.conf import settings

from rest_framework import serializers
from bookings.models import Booking
from cases.models import CaseCategory
from base.constants.booking_status import BookingStatus
from base.constants.verification import VerificationStatus
from bookings.models import Booking
from django.contrib.auth import get_user_model

User = get_user_model()



class BookingCreateSerializer(serializers.ModelSerializer):
    created_to = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_active=True)
    )

    case_category = serializers.PrimaryKeyRelatedField(
        queryset=CaseCategory.objects.filter(is_active=True)
    )

    class Meta:
        model = Booking
        fields = [
            "id",
            "created_to",
            "case_category",
            "court_type",
            "description",
            "date",
        ]

    def validate(self, attrs):
        request = self.context.get("request")
        created_by = request.user
        created_to = attrs.get("created_to")

        if created_by == created_to:
            raise serializers.ValidationError(
                "You cannot create a booking for yourself."
            )

        return attrs
    


class BookingActorSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    role = serializers.CharField(read_only=True)

    @staticmethod
    def get_actor_data(user):
        """
        Returns unified, verified actor representation for booking APIs.
        Assumes only VERIFIED users can participate in bookings.
        """

        if user.role == "lawyer":
            verification = getattr(user, "bar_verification", None)
            profile = getattr(user, "lawyer_profile", None)

            if not verification or verification.status != VerificationStatus.VERIFIED:
                raise ValueError("Unverified lawyer cannot be used in booking actor")

            return {
                "id": profile.id,
                "name": verification.full_name,
                "email": user.email,
                "role": user.role,
            }

        if user.role == "firm":
            verification = getattr(user, "firm_verification", None)
            profile = getattr(user, "firm_profile", None)

            if not verification or verification.status != VerificationStatus.VERIFIED:
                raise ValueError("Unverified firm cannot be used in booking actor")

            return {
                "id": profile.id,
                "name": verification.firm_name,
                "email": user.email,
                "role": user.role,
            }

        if user.role == "client":
            verification = getattr(user, "client_verification", None)
            profile = getattr(user, "client_profile", None)

            if not verification or verification.status != VerificationStatus.VERIFIED:
                raise ValueError("Unverified client cannot be used in booking actor")

            return {
                "id": profile.id,
                "name": verification.full_name,
                "email": user.email,
                "role": user.role,
            }

        raise ValueError("Unsupported user role for booking actor")




class BookingListSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField()
    created_to = serializers.SerializerMethodField()
    case_category_name = serializers.CharField(
        source="case_category.name",
        read_only=True
    )

    class Meta:
        model = Booking
        fields = [
            "id",
            "created_by",
            "created_to",
            "date",
            "status",
            "court_type",
            "case_category_name",
            "created_at",
        ]

    def get_created_by(self, obj):
        return BookingActorSerializer.get_actor_data(obj.created_by)

    def get_created_to(self, obj):
        return BookingActorSerializer.get_actor_data(obj.created_to)


class BookingDetailSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField()
    created_to = serializers.SerializerMethodField()
    case_category_name = serializers.CharField(
        source="case_category.name",
        read_only=True
    )

    class Meta:
        model = Booking
        fields = [
            "id",
            "created_by",
            "created_to",
            "case_category",
            "case_category_name",
            "court_type",
            "description",
            "date",
            "status",
            "created_at",
        ]
        read_only_fields = [
            "status",
            "created_at",
        ]

    def get_created_by(self, obj):
        return BookingActorSerializer.get_actor_data(obj.created_by)

    def get_created_to(self, obj):
        return BookingActorSerializer.get_actor_data(obj.created_to)


class BookingStatusActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(
        choices=[
            BookingStatus.ACCEPTED,
            BookingStatus.REJECTED,
        ]
    )

    def validate(self, attrs):
        booking = self.context.get("booking")

        if booking.status != BookingStatus.PENDING:
            raise serializers.ValidationError(
                "Only pending bookings can be responded to."
            )

        return attrs
