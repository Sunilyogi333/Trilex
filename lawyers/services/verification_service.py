# lawyers/services/verification_service.py

from rest_framework.exceptions import ValidationError
from lawyers.models import BarVerification


class LawyerVerificationService:
    """
    Handles lawyer bar verification lifecycle.
    """

    @staticmethod
    def submit(user, **data):
        verification = BarVerification.objects.filter(user=user).first()

        if verification:
            if verification.status == BarVerification.Status.PENDING:
                raise ValidationError("Verification already under review.")

            if verification.status == BarVerification.Status.VERIFIED:
                raise ValidationError("Lawyer already verified.")

            # rejected → resubmit
            for field, value in data.items():
                setattr(verification, field, value)

            verification.status = BarVerification.Status.PENDING
            verification.rejection_reason = None
            verification.save()
            return verification

        return BarVerification.objects.create(
            user=user,
            status=BarVerification.Status.PENDING,
            **data
        )

    @staticmethod
    def approve(verification: BarVerification):
        verification.status = BarVerification.Status.VERIFIED
        verification.rejection_reason = None
        verification.save(update_fields=["status", "rejection_reason"])

    @staticmethod
    def reject(verification: BarVerification, reason: str):
        if not reason:
            raise ValidationError("Rejection reason is required.")

        verification.status = BarVerification.Status.REJECTED
        verification.rejection_reason = reason
        verification.save(update_fields=["status", "rejection_reason"])
