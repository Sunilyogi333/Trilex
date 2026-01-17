from rest_framework.exceptions import ValidationError
from clients.models import ClientIDVerification


class ClientVerificationService:

    # ---------- Client ----------
    @staticmethod
    def submit_verification(user, **data):
        verification = ClientIDVerification.objects.filter(user=user).first()

        if verification:
            if verification.status == ClientIDVerification.Status.PENDING:
                raise ValidationError("Verification already submitted.")

            if verification.status == ClientIDVerification.Status.VERIFIED:
                raise ValidationError("Client already verified.")

            # REJECTED → allow resubmission
            for field, value in data.items():
                setattr(verification, field, value)

            verification.status = ClientIDVerification.Status.PENDING
            verification.rejection_reason = None
            verification.save()
            return verification

        return ClientIDVerification.objects.create(
            user=user,
            **data
        )

    # ---------- Admin ----------
    @staticmethod
    def approve(verification):
        verification.status = ClientIDVerification.Status.VERIFIED
        verification.rejection_reason = None
        verification.save()

    @staticmethod
    def reject(verification, reason):
        verification.status = ClientIDVerification.Status.REJECTED
        verification.rejection_reason = reason
        verification.save()


    # ---------- CREATE ----------
    @staticmethod
    def create_verification(user, **data):
        if ClientIDVerification.objects.filter(user=user).exists():
            raise ValidationError(
                "Verification already exists. Use update after rejection."
            )

        return ClientIDVerification.objects.create(
            user=user,
            status=ClientIDVerification.Status.PENDING,
            **data
        )

    # ---------- UPDATE / RESUBMIT ----------
    @staticmethod
    def update_verification(user, **data):
        verification = ClientIDVerification.objects.filter(user=user).first()

        if not verification:
            raise ValidationError("No verification found to update.")

        if verification.status != ClientIDVerification.Status.REJECTED:
            raise ValidationError(
                "Verification can only be updated after rejection."
            )

        # partial overwrite
        for field, value in data.items():
            if value is not None:
                setattr(verification, field, value)

        verification.status = ClientIDVerification.Status.PENDING
        verification.rejection_reason = None
        verification.save()

        return verification