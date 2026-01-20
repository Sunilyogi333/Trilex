# addresses/models/district.py
from django.db import models
from .province import Province

class District(models.Model):
    province = models.ForeignKey(
        Province,
        on_delete=models.CASCADE,
        related_name="districts"
    )
    title = models.CharField(max_length=100)
    title_nepali = models.CharField(max_length=100)
    code = models.PositiveSmallIntegerField(unique=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title
