from django.db import models


class VerificationStatus(models.TextChoices):
    NOT_SUBMITTED = "NOT_SUBMITTED", "Not Submitted"
    PENDING = "PENDING", "Pending"
    VERIFIED = "VERIFIED", "Verified"
    REJECTED = "REJECTED", "Rejected"
