# firms/models.py

from django.conf import settings
from django.db import models
from base.models import AbstractBaseModel
from media.models import Image
from base.constants.verification import VerificationStatus
from cases.models import CaseCategory
from addresses.models import Address

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
    address = models.OneToOneField(
        Address,
        on_delete=models.CASCADE,
        related_name="firm",
    )
    services = models.ManyToManyField(
        CaseCategory,
        related_name="firms"
    )

    def __str__(self):
        return f"Firm({self.user.email})"


class FirmVerification(AbstractBaseModel):
    """
    Firm legal verification (KYB).
    Source of truth for firm identity.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="firm_verification"
    )

    # immutable firm identity
    firm_name = models.CharField(max_length=255)
    owner_name = models.CharField(max_length=255)
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
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING
    )
    rejection_reason = models.TextField(
        blank=True,
        null=True
    )

    def __str__(self):
        return f"FirmVerification({self.firm_name}, {self.status})"
