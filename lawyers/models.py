# lawyers/models.py

from django.conf import settings
from django.db import models
from base.models import AbstractBaseModel
from media.models import Image

User = settings.AUTH_USER_MODEL


class Lawyer(AbstractBaseModel):
    """
    Lawyer profile.
    Only mutable / operational fields.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="lawyer_profile"
    )

    phone_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return f"Lawyer({self.user.email})"


class BarVerification(AbstractBaseModel):
    """
    Lawyer bar verification.
    Source of truth for lawyer identity.
    """

    class Status(models.TextChoices):
        NOT_SUBMITTED = "NOT_SUBMITTED", "Not Submitted"
        PENDING = "PENDING", "Pending"
        VERIFIED = "VERIFIED", "Verified"
        REJECTED = "REJECTED", "Rejected"

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="bar_verification"
    )

    # immutable legal identity
    full_name = models.CharField(max_length=255)
    date_of_birth = models.DateField()
    bar_id = models.CharField(max_length=100, unique=True)
    gender = models.CharField(max_length=20)

    # ---- License document (Cloudinary-backed) ----
    license_photo = models.OneToOneField(
        Image,
        on_delete=models.SET_NULL,
        null=True,
        related_name="lawyer_license"
    )
    # lifecycle
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    rejection_reason = models.TextField(
        blank=True,
        null=True
    )

    def __str__(self):
        return f"BarVerification({self.user.email}, {self.status})"
