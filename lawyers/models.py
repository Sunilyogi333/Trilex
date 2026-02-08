from django.conf import settings
from django.db import models
from base.models import AbstractBaseModel
from media.models import Image
from base.constants.verification import VerificationStatus
from cases.models import CaseCategory
from addresses.models.address import Address

User = settings.AUTH_USER_MODEL

class Lawyer(AbstractBaseModel):
    """
    Lawyer profile.
    Mutable / operational fields only.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="lawyer_profile"
    )

    phone_number = models.CharField(max_length=20, blank=True)

    address = models.OneToOneField(
        Address,
        on_delete=models.CASCADE,
        related_name="lawyer",
    )

    # Services lawyer provides
    services = models.ManyToManyField(
        CaseCategory,
        related_name="lawyers"
    )

    def __str__(self):
        return f"Lawyer({self.user.email})"


class BarVerification(AbstractBaseModel):
    """
    Lawyer bar verification.
    Source of truth for lawyer identity.
    """

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
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING
    )
    rejection_reason = models.TextField(
        blank=True,
        null=True
    )

    def __str__(self):
        return f"BarVerification({self.user.email}, {self.status})"
