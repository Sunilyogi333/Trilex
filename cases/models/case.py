from django.conf import settings
from django.db import models

from base.models import AbstractBaseModel
from base.constants.case import CaseOwnerType, CourtType, CaseStatus
from cases.models.case_category import CaseCategory

User = settings.AUTH_USER_MODEL


class Case(AbstractBaseModel):
    """
    Core case model.
    Holds ownership, legal metadata, and relations.
    """

    # --------------------
    # Ownership
    # --------------------
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

    # --------------------
    # Case metadata
    # --------------------
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

    # --------------------
    # Client profile link (UPDATED)
    # --------------------
    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cases"
    )

    def __str__(self):
        return f"Case({self.title})"
