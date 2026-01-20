# addresses/models/ward.py
from django.db import models
from .municipality import Municipality

class Ward(models.Model):
    municipality = models.ForeignKey(
        Municipality,
        on_delete=models.CASCADE,
        related_name="wards"
    )
    number = models.PositiveSmallIntegerField()
    number_nepali = models.CharField(max_length=10)

    class Meta:
        unique_together = ("municipality", "number")
        ordering = ["number"]

    def __str__(self):
        return f"Ward {self.number}"
