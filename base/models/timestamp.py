from django.db import models


class Timestamps(models.Model):

    class Meta:
        abstract = True

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        db_index=True,
    )
