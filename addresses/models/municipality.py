# addresses/models/municipality.py
from django.db import models
from .district import District

class Municipality(models.Model):
    district = models.ForeignKey(
        District,
        on_delete=models.CASCADE,
        related_name="municipalities"
    )
    title = models.CharField(max_length=150)
    title_nepali = models.CharField(max_length=150)
    code = models.PositiveIntegerField(unique=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title
