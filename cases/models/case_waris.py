from django.db import models

from base.models import AbstractBaseModel
from cases.models.case import Case


class CaseWaris(AbstractBaseModel):
    """
    Immutable snapshot of waris details for a case.
    Optional – zero or one per case.
    """

    case = models.OneToOneField(
        Case,
        on_delete=models.CASCADE,
        related_name="waris"
    )

    full_name = models.CharField(max_length=255)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    citizenship_number = models.CharField(max_length=100, blank=True)
    gender = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"CaseWaris({self.full_name})"
