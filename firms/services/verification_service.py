# firms/services/verification_service.py

from rest_framework.exceptions import ValidationError
from firms.models import FirmVerification


class FirmVerificationService:
    """
    Handles firm verification lifecycle.
    """

    @staticmethod
    def submit(user, **data):
        verification = FirmVerification.objects.filter(user=user).first()

        if verification:
            if verification.status == FirmVerification.Status.PENDING:
                raise ValidationError("Verification already under review.")

            if verification.status == FirmVerification.Status.VERIFIED:
                raise ValidationError("Firm already verified.")

            # rejected → resubmit
            for field, value in data.items():
                setattr(verification, field, value)

            verification.status = FirmVerification.Status.PENDING
            verification.rejection_reason = None
            verification.save()
            return verification

        return FirmVerification.objects.create(
            user=user,
            status=FirmVerification.Status.PENDING,
            **data
        )

    @staticmethod
    def approve(verification: FirmVerification):
        verification.status = FirmVerification.Status.VERIFIED
        verification.rejection_reason = None
        verification.save(update_fields=["status", "rejection_reason"])

    @staticmethod
    def reject(verification: FirmVerification, reason: str):
        if not reason:
            raise ValidationError("Rejection reason is required.")

        verification.status = FirmVerification.Status.REJECTED
        verification.rejection_reason = reason
        verification.save(update_fields=["status", "rejection_reason"])
