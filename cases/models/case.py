from django.conf import settings
from django.db import models

from base.models import AbstractBaseModel
from cases.models.case_category import CaseCategory
from base.constants.case import CaseOwnerType, CourtType, CaseStatus

User = settings.AUTH_USER_MODEL

class Case(AbstractBaseModel):
    # ---- ownership ----
    owner_type = models.CharField(
        max_length=20,
        choices=CaseOwnerType.choices
    )

    owner_lawyer = models.ForeignKey(
       "lawyers.Lawyer",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="solo_cases"
    )

    owner_firm = models.ForeignKey(
       "firms.Firm",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="firm_cases"
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_cases"
    )

    # ---- general case info ----
    title = models.CharField(max_length=255)

    case_category = models.ForeignKey(
        CaseCategory,
        on_delete=models.PROTECT,
        related_name="cases"
    )

    court_type = models.CharField(
        max_length=20,
        choices=CourtType.choices
    )

    description = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=CaseStatus.choices,
        default=CaseStatus.DRAFT
    )

    # ---- client snapshot (REQUIRED) ----
    client_full_name = models.CharField(max_length=255)
    client_address = models.CharField(max_length=255)
    client_email = models.EmailField()
    client_phone = models.CharField(max_length=20)
    client_date_of_birth = models.DateField()
    client_citizenship_number = models.CharField(max_length=100)
    client_gender = models.CharField(max_length=20)

    client_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="client_cases"
    )

    # ---- waris snapshot (OPTIONAL) ----
    waris_full_name = models.CharField(max_length=255, blank=True)
    waris_email = models.EmailField(blank=True)
    waris_address = models.CharField(max_length=255, blank=True)
    waris_phone = models.CharField(max_length=20, blank=True)
    waris_date_of_birth = models.DateField(null=True, blank=True)
    waris_citizenship_number = models.CharField(max_length=100, blank=True)
    waris_gender = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"Case({self.title})"
