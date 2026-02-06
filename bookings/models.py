from django.db import models
from django.conf import settings
from base.models import AbstractBaseModel
from cases.models import CaseCategory
from base.constants.court_types import CourtType
from base.constants.booking_status import BookingStatus


class Booking(AbstractBaseModel):
    """
    Booking created by a client and sent to a lawyer or firm
    """

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_bookings"
    )

    created_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_bookings"
    )

    case_category = models.ForeignKey(
        CaseCategory,
        on_delete=models.PROTECT,
        related_name="bookings"
    )

    court_type = models.CharField(
        max_length=20,
        choices=CourtType.choices
    )

    description = models.TextField()

    date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=BookingStatus.choices,
        default=BookingStatus.PENDING
    )

    class Meta:
        db_table = "bookings"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["created_by"]),
            models.Index(fields=["created_to"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"Booking {self.id} ({self.status})"
