from django.conf import settings
from django.db import models
from base.models import AbstractBaseModel
from cases.models import CaseCategory
from addresses.models import Address

User = settings.AUTH_USER_MODEL


class Firm(AbstractBaseModel):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="firm_profile"
    )

    phone_number = models.CharField(max_length=20, blank=True)
    address = models.OneToOneField(
        Address,
        on_delete=models.CASCADE,
        related_name="firm",
    )
    services = models.ManyToManyField(
        CaseCategory,
        related_name="firms"
    )

    def __str__(self):
        return f"Firm({self.user.email})"