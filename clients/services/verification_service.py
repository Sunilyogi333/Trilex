# clients/services/verification_service.py

from rest_framework.exceptions import ValidationError

from clients.models import IDVerification
from base.constants.verification import VerificationStatus


class ClientVerificationService:
    """
    Handles client ID verification lifecycle.

    Rules:
    - VERIFIED clients cannot be re-approved or rejected
    - PENDING verifications cannot be resubmitted
    - REJECTED verifications must be resubmitted before approval
    """

    # -------------------------
    # SUBMIT / RESUBMIT
    # -------------------------
    @staticmethod
    def submit(user, **data):
        verification = IDVerification.objects.filter(user=user).first()

        if verification:
            if verification.status == VerificationStatus.PENDING:
                raise ValidationError(
                    "Verification is already under review."
                )

            if verification.status == VerificationStatus.VERIFIED:
                raise ValidationError(
                    "Client is already verified."
                )

            # REJECTED → allow resubmission
            for field, value in data.items():
                setattr(verification, field, value)

            verification.status = VerificationStatus.PENDING
            verification.rejection_reason = None
            verification.save()
            return verification

        # First-time submission
        return IDVerification.objects.create(
            user=user,
            status=VerificationStatus.PENDING,
            **data
        )

    # -------------------------
    # ADMIN: APPROVE
    # -------------------------
    @staticmethod
    def approve(verification: IDVerification):
        if verification.status == VerificationStatus.VERIFIED:
            raise ValidationError("Client is already verified.")

        if verification.status == VerificationStatus.REJECTED:
            raise ValidationError(
                "Rejected verification must be resubmitted before approval."
            )

        verification.status = VerificationStatus.VERIFIED
        verification.rejection_reason = None
        verification.save(update_fields=["status", "rejection_reason"])

    # -------------------------
    # ADMIN: REJECT
    # -------------------------
    @staticmethod
    def reject(verification: IDVerification, reason: str):
        if verification.status == VerificationStatus.VERIFIED:
            raise ValidationError(
                "Verified client cannot be rejected."
            )

        if not reason:
            raise ValidationError("Rejection reason is required.")

        verification.status = VerificationStatus.REJECTED
        verification.rejection_reason = reason
        verification.save(update_fields=["status", "rejection_reason"])

    # -------------------------
    # READ
    # -------------------------
    @staticmethod
    def get_status(user):
        verification = IDVerification.objects.filter(user=user).first()
        if not verification:
            return VerificationStatus.NOT_SUBMITTED

        return verification.status
