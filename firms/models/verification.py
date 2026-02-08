from django.conf import settings
from django.db import models
from base.models import AbstractBaseModel
from media.models import Image
from base.constants.verification import VerificationStatus

User = settings.AUTH_USER_MODEL

class FirmVerification(AbstractBaseModel):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="firm_verification"
    )

    firm_name = models.CharField(max_length=255)
    owner_name = models.CharField(max_length=255)
    firm_id = models.CharField(max_length=100)
    firm_license = models.OneToOneField(
        Image,
        on_delete=models.SET_NULL,
        null=True,
        related_name="firm_license"
    )

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
