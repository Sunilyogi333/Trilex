
from django.db import models

class CourtType(models.TextChoices):
    DISTRICT = "district", "District"
    HIGH = "high", "High"
    SUPREME = "supreme", "Supreme"