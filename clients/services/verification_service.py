from rest_framework.exceptions import ValidationError

from clients.models import IDVerification

class ClientVerificationService:
    """
    Handles client ID verification lifecycle.
    """

    # ---------- SUBMIT / CREATE ----------
    @staticmethod
    def submit(user, **data):
        """
        Submit verification for the first time
        OR resubmit after rejection.
        """

        verification = IDVerification.objects.filter(user=user).first()

        # Already exists
        if verification:
            if verification.status == IDVerification.Status.PENDING:
                raise ValidationError(
                    "Verification is already under review."
                )

            if verification.status == IDVerification.Status.VERIFIED:
                raise ValidationError(
                    "Client is already verified."
                )

            # REJECTED → allow resubmission
            for field, value in data.items():
                setattr(verification, field, value)

            verification.status = IDVerification.Status.PENDING
            verification.rejection_reason = None
            verification.save()
            return verification

        # First-time submission
        return IDVerification.objects.create(
            user=user,
            status=IDVerification.Status.PENDING,
            **data
        )

    # ---------- ADMIN ACTIONS ----------
    @staticmethod
    def approve(verification: IDVerification):
        if verification.status == IDVerification.Status.VERIFIED:
            raise ValidationError("Client already verified.")

        verification.status = IDVerification.Status.VERIFIED
        verification.rejection_reason = None
        verification.save(update_fields=["status", "rejection_reason"])

    @staticmethod
    def reject(verification: IDVerification, reason: str):
        if not reason:
            raise ValidationError("Rejection reason is required.")

        verification.status = IDVerification.Status.REJECTED
        verification.rejection_reason = reason
        verification.save(update_fields=["status", "rejection_reason"])

    # ---------- READ ----------
    @staticmethod
    def get_status(user):
        """
        Returns verification status for the client.
        """
        verification = IDVerification.objects.filter(user=user).first()
        if not verification:
            return IDVerification.Status.NOT_SUBMITTED

        return verification.status
