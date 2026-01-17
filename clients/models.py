from django.db import models
from django.conf import settings
from base.models import AbstractBaseModel

User = settings.AUTH_USER_MODEL


class ClientIDVerification(AbstractBaseModel):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        VERIFIED = "VERIFIED", "Verified"
        REJECTED = "REJECTED", "Rejected"

    class IDType(models.TextChoices):
        PASSPORT = "PASSPORT", "Passport"
        NATIONAL_ID = "NATIONAL_ID", "National ID"
        CITIZENSHIP = "CITIZENSHIP", "Citizenship"

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="client_verification"
    )

    # legal identity snapshot
    full_name = models.CharField(max_length=255)
    date_of_birth = models.DateField()

    # ID document
    id_type = models.CharField(
        max_length=30,
        choices=IDType.choices
    )
    passport_size_photo = models.ImageField(
        upload_to="client_verification/passport/"
    )
    photo_front = models.ImageField(
        upload_to="client_verification/front/"
    )
    photo_back = models.ImageField(
        upload_to="client_verification/back/"
    )

    # verification lifecycle
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
        return f"{self.user} - {self.status}"
