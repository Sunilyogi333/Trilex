from django.conf import settings
from django.db import models
from base.models import AbstractBaseModel
from cases.models import CaseCategory
from addresses.models.address import Address

User = settings.AUTH_USER_MODEL

class Lawyer(AbstractBaseModel):
    """
    Lawyer profile.
    Mutable / operational fields only.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="lawyer_profile"
    )

    phone_number = models.CharField(max_length=20, blank=True)

    address = models.OneToOneField(
        Address,
        on_delete=models.CASCADE,
        related_name="lawyer",
    )

    # Services lawyer provides
    services = models.ManyToManyField(
        CaseCategory,
        related_name="lawyers"
    )

    def __str__(self):
        return f"Lawyer({self.user.email})"