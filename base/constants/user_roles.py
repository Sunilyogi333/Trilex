from django.db import models

class UserRoles(models.TextChoices):
    CLIENT = "client", "Client"
    LAWYER = "lawyer", "Lawyer"
    FIRM = "firm", "Firm Admin"
    ADMIN = "admin", "Administrator"