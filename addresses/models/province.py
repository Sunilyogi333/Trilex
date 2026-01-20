# addresses/models/province.py
from django.db import models

class Province(models.Model):
    title = models.CharField(max_length=100)
    title_nepali = models.CharField(max_length=100)
    code = models.PositiveSmallIntegerField(unique=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return self.title
