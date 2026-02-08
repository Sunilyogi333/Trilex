from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError

from base.constants.verification import VerificationStatus
from base.constants.firm_invitation_status import FirmInvitationStatus
from firms.models import Firm, FirmInvitation, FirmMember
from lawyers.models import Lawyer


class FirmInvitationService:
    @staticmethod
    @transaction.atomic
    def invite_lawyer(*, firm: Firm, lawyer: Lawyer) -> FirmInvitation:
        lawyer_verification = getattr(lawyer.user, "bar_verification", None)
        if (
            not lawyer_verification
            or lawyer_verification.status != VerificationStatus.VERIFIED
        ):
            raise ValidationError("Lawyer is not verified")

        if hasattr(lawyer, "firm_membership"):
            if lawyer.firm_membership.firm_id == firm.id:
                raise ValidationError("Lawyer already belongs to this firm")

        existing_pending = FirmInvitation.objects.filter(
            firm=firm,
            lawyer=lawyer,
            status=FirmInvitationStatus.PENDING,
        ).exists()

        if existing_pending:
            raise ValidationError("Pending invitation already exists")

        invitation = FirmInvitation.objects.create(
            firm=firm,
            lawyer=lawyer,
            status=FirmInvitationStatus.PENDING,
        )

        return invitation

    @staticmethod
    @transaction.atomic
    def accept_invitation(*, invitation: FirmInvitation) -> FirmMember:
        if invitation.status != FirmInvitationStatus.PENDING:
            raise ValidationError("Invitation is not pending")

        lawyer = invitation.lawyer
        firm = invitation.firm

        if hasattr(lawyer, "firm_membership"):
            raise ValidationError(
                "Lawyer already belongs to another firm. Leave current firm to accept."
            )

        firm_verification = getattr(firm.user, "firm_verification", None)
        if (
            not firm_verification
            or firm_verification.status != VerificationStatus.VERIFIED
        ):
            raise ValidationError("Firm is not verified")

        member = FirmMember.objects.create(
            firm=firm,
            lawyer=lawyer,
        )

        invitation.status = FirmInvitationStatus.ACCEPTED
        invitation.responded_at = timezone.now()
        invitation.save(update_fields=["status", "responded_at"])

        return member

    @staticmethod
    @transaction.atomic
    def reject_invitation(*, invitation: FirmInvitation) -> FirmInvitation:
        if invitation.status != FirmInvitationStatus.PENDING:
            raise ValidationError("Invitation is not pending")

        invitation.status = FirmInvitationStatus.REJECTED
        invitation.responded_at = timezone.now()
        invitation.save(update_fields=["status", "responded_at"])

        return invitation
