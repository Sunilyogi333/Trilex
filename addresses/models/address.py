# addresses/models/address.py
from django.db import models
from base.models import AbstractBaseModel
from .province import Province
from .district import District
from .municipality import Municipality
from .ward import Ward

class Address(AbstractBaseModel):
    province = models.ForeignKey(Province, on_delete=models.PROTECT)
    district = models.ForeignKey(District, on_delete=models.PROTECT)
    municipality = models.ForeignKey(Municipality, on_delete=models.PROTECT)
    ward = models.ForeignKey(Ward, on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.municipality}, Ward {self.ward.number}"
