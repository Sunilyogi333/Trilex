from django.conf import settings
from django.db import models
from django.db.models import UniqueConstraint

from base.models import AbstractBaseModel
from lawyers.models import Lawyer
from firms.models import Firm

User = settings.AUTH_USER_MODEL


class FirmMember(AbstractBaseModel):
    firm = models.ForeignKey(
        Firm,
        on_delete=models.CASCADE,
        related_name="members"
    )

    lawyer = models.OneToOneField(
        Lawyer,
        on_delete=models.CASCADE,
        related_name="firm_membership"
    )

    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["lawyer"],
                name="unique_lawyer_firm_membership"
            )
        ]

    def __str__(self):
        return f"{self.lawyer.user.email} -> {self.firm.user.email}"
