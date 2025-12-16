from django.db import models
from django.utils import timezone


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                deleted_at__isnull=True,
            )
        )


class SoftDelete(models.Model):
    objects = SoftDeleteManager()

    class Meta:
        abstract = True

    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        default=None,
    )

    def soft_delete(self):
        self.deleted_at = timezone.now()
        self.save()
