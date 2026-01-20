from django.db import models
from base.models import AbstractBaseModel


class CaseCategory(AbstractBaseModel):
    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "case_categories"
        ordering = ["name"]

    def __str__(self):
        return self.name
