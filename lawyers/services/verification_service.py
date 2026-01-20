# lawyers/services/verification_service.py

from rest_framework.exceptions import ValidationError
from lawyers.models import BarVerification
from base.constants.verification import VerificationStatus


class LawyerVerificationService:
    """
    Handles lawyer bar verification lifecycle.
    """

    # -------------------------
    # SUBMIT / RESUBMIT
    # -------------------------
    @staticmethod
    def submit(user, **data):
        verification = BarVerification.objects.filter(user=user).first()

        if verification:
            if verification.status == VerificationStatus.PENDING:
                raise ValidationError("Verification already under review.")

            if verification.status == VerificationStatus.VERIFIED:
                raise ValidationError("Lawyer already verified.")

            # REJECTED → resubmit
            for field, value in data.items():
                setattr(verification, field, value)

            verification.status = VerificationStatus.PENDING
            verification.rejection_reason = None
            verification.save()
            return verification

        return BarVerification.objects.create(
            user=user,
            status=VerificationStatus.PENDING,
            **data
        )

    # -------------------------
    # ADMIN: APPROVE
    # -------------------------
    @staticmethod
    def approve(verification: BarVerification):
        if verification.status == VerificationStatus.VERIFIED:
            raise ValidationError("Lawyer already verified.")

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
    def reject(verification: BarVerification, reason: str):
        if verification.status == VerificationStatus.VERIFIED:
            raise ValidationError(
                "Verified lawyer cannot be rejected."
            )

        if not reason:
            raise ValidationError("Rejection reason is required.")

        verification.status = VerificationStatus.REJECTED
        verification.rejection_reason = reason
        verification.save(update_fields=["status", "rejection_reason"])
