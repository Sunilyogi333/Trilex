# firms/services/verification_service.py

from rest_framework.exceptions import ValidationError
from firms.models import FirmVerification
from base.constants.verification import VerificationStatus


class FirmVerificationService:
    """
    Handles firm verification lifecycle.
    """

    @staticmethod
    def submit(user, **data):
        verification = FirmVerification.objects.filter(user=user).first()

        if verification:
            if verification.status == VerificationStatus.PENDING:
                raise ValidationError("Verification already under review.")

            if verification.status == VerificationStatus.VERIFIED:
                raise ValidationError("Firm already verified.")

            # rejected → resubmit
            for field, value in data.items():
                setattr(verification, field, value)

            verification.status = VerificationStatus.PENDING
            verification.rejection_reason = None
            verification.save()
            return verification

        return FirmVerification.objects.create(
            user=user,
            status=VerificationStatus.PENDING,
            **data
        )


    # -------------------------
    # ADMIN: APPROVE
    # -------------------------
    @staticmethod
    def approve(verification: FirmVerification):
        if verification.status == VerificationStatus.VERIFIED:
            raise ValidationError("Firm is already verified.")

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
    def reject(verification: FirmVerification, reason: str):
        if verification.status == VerificationStatus.VERIFIED:
            raise ValidationError(
                "Verified firm cannot be rejected."
            )

        if not reason:
            raise ValidationError("Rejection reason is required.")

        verification.status = VerificationStatus.REJECTED
        verification.rejection_reason = reason
        verification.save(update_fields=["status", "rejection_reason"])
