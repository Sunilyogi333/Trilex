from django.contrib.auth.models import AbstractUser
from django.db import models

from accounts.managers import UserManager
from base.models import AbstractBaseModel
from base.constants.user_roles import UserRoles


class User(AbstractUser, AbstractBaseModel):
    username = None
    first_name = None
    last_name = None

    email = models.EmailField(unique=True)

    role = models.CharField(
        max_length=20,
        choices=UserRoles.choices
    )

    is_email_verified = models.BooleanField(default=False)
    otp_secret = models.CharField(max_length=32, null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return f"{self.email} ({self.role})"
