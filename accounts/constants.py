from django.db import models

class UserRoles(models.TextChoices):
    GUEST = "guest", "Guest User"
    GENERAL = "general", "General User"
    LAWYER = "lawyer", "Lawyer"
    FIRM = "firm", "Firm Admin"
    ADMIN = "client_admin", "Client Administrator"

