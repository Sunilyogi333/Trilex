# firms/models.py

from django.conf import settings
from django.db import models
from base.models import AbstractBaseModel
from media.models import Image

User = settings.AUTH_USER_MODEL


class Firm(AbstractBaseModel):
    """
    Firm profile.
    Stores only mutable / operational fields.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="firm_profile"
    )

    phone_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return f"Firm({self.user.email})"


class FirmVerification(AbstractBaseModel):
    """
    Firm legal verification (KYB).
    Source of truth for firm identity.
    """

    class Status(models.TextChoices):
        NOT_SUBMITTED = "NOT_SUBMITTED", "Not Submitted"
        PENDING = "PENDING", "Pending"
        VERIFIED = "VERIFIED", "Verified"
        REJECTED = "REJECTED", "Rejected"

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="firm_verification"
    )

    # immutable firm identity
    firm_name = models.CharField(max_length=255)
    owner_name = models.CharField(max_length=255)
    firm_email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    firm_id = models.CharField(max_length=100)
    firm_license = models.OneToOneField(
        Image,
        on_delete=models.SET_NULL,
        null=True,
        related_name="firm_license"
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
        return f"FirmVerification({self.firm_name}, {self.status})"
