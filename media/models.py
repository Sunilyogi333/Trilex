# media/models.py

from django.db import models
from base.models import AbstractBaseModel


class Image(AbstractBaseModel):
    """
    Minimal Cloudinary-backed image reference.
    """
    url = models.URLField()

    def __str__(self):
        return self.url
