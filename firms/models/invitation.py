from django.db import models
from django.db.models import UniqueConstraint

from base.models import AbstractBaseModel
from lawyers.models import Lawyer
from firms.models import Firm
from base.constants.firm_invitation_status import FirmInvitationStatus

class FirmInvitation(AbstractBaseModel):
    firm = models.ForeignKey(
        Firm,
        on_delete=models.CASCADE,
        related_name="sent_invitations"
    )

    lawyer = models.ForeignKey(
        Lawyer,
        on_delete=models.CASCADE,
        related_name="received_invitations"
    )

    status = models.CharField(
        max_length=20,
        choices=FirmInvitationStatus.choices,
        default=FirmInvitationStatus.PENDING
    )

    invited_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["firm", "lawyer"],
                condition=models.Q(status="pending"),
                name="unique_pending_firm_invitation"
            )
        ]
        ordering = ["-invited_at"]

    def __str__(self):
        return (
            f"Invitation({self.firm.user.email} -> "
            f"{self.lawyer.user.email}, {self.status})"
        )
