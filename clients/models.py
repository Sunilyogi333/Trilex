from django.conf import settings
from django.db import models

from base.models import AbstractBaseModel
from media.models import Image
from base.constants.verification import VerificationStatus
from base.constants.client_id_type import ClientIDType

User = settings.AUTH_USER_MODEL


class Client(AbstractBaseModel):
    """
    Client profile.
    Stores only mutable / operational fields.
    Identity fields are NOT allowed here.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="client_profile"
    )

    phone_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return f"Client({self.user.email})"


class IDVerification(AbstractBaseModel):
    """
    Client identity verification (KYC).
    Source of truth for legal identity.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="client_verification"
    )

    # ---- Legal identity snapshot (immutable after approval) ----
    full_name = models.CharField(max_length=255)
    date_of_birth = models.DateField()

    id_type = models.CharField(
        max_length=30,
        choices=ClientIDType.choices
    )

    passport_size_photo = models.OneToOneField(
        Image,
        on_delete=models.SET_NULL,
        null=True,
        related_name="passport_size_photo"
    )

    photo_front = models.OneToOneField(
        Image,
        on_delete=models.SET_NULL,
        null=True,
        related_name="client_id_front"
    )

    photo_back = models.OneToOneField(
        Image,
        on_delete=models.SET_NULL,
        null=True,
        related_name="client_id_back"
    )

    # ---- Verification lifecycle ----
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
        return f"IDVerification({self.user.email}, {self.status})"
