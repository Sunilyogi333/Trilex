from django.db import models

class ClientIDType(models.TextChoices):
        NATIONAL_ID = "NATIONAL_ID", "National ID"
        CITIZENSHIP = "CITIZENSHIP", "Citizenship"