from django.db import models

from base.models import AbstractBaseModel
from cases.models.case import Case
from base.constants.case import CaseLawyerRole

class CaseLawyer(AbstractBaseModel):
    case = models.ForeignKey(
        Case,
        on_delete=models.CASCADE,
        related_name="assigned_lawyers"
    )

    lawyer = models.ForeignKey(
        "lawyers.Lawyer",
        on_delete=models.CASCADE,
        related_name="case_assignments"
    )

    role = models.CharField(
        max_length=20,
        choices=CaseLawyerRole.choices,
        default=CaseLawyerRole.ASSISTANT
    )

    can_edit = models.BooleanField(default=True)

    class Meta:
        unique_together = ("case", "lawyer")

    def __str__(self):
        return f"{self.lawyer.user.email} -> {self.case.title}"
