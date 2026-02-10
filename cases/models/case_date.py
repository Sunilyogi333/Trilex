from django.db import models

from base.models import AbstractBaseModel
from cases.models.case import Case
from base.constants.case import CaseDateType

class CaseDate(AbstractBaseModel):
    case = models.ForeignKey(
        Case,
        on_delete=models.CASCADE,
        related_name="dates"
    )

    date_type = models.CharField(
        max_length=20,
        choices=CaseDateType.choices
    )

    date = models.DateField()

    remark = models.TextField(blank=True)

    assigned_to_name = models.CharField(
        max_length=255,
        blank=True
    )

    def __str__(self):
        return f"{self.case.title} - {self.date_type} - {self.date}"
