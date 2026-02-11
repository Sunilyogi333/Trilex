from django.db import models
from base.models import AbstractBaseModel
from cases.models.case import Case


class CaseClientDetails(AbstractBaseModel):
    """
    Immutable snapshot of client details for a case.
    Exactly ONE snapshot per case.
    """

    case = models.OneToOneField(
        Case,
        on_delete=models.CASCADE,
        related_name="client_details"
    )

    full_name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    date_of_birth = models.DateField()
    citizenship_number = models.CharField(max_length=100)
    gender = models.CharField(max_length=20)

    def __str__(self):
        return f"CaseClientDetails({self.full_name})"
