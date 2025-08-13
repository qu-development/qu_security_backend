from django.db import models
from django.utils import timezone


class ActiveManager(models.Manager):
    """Default manager that only returns active records."""

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class BaseModel(models.Model):
    """
    Abstract base model that provides common fields for all models.
    Includes automatic timestamp tracking and soft delete functionality.
    """

    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    # Managers: by default, only active records are returned
    all_objects = models.Manager()
    objects = ActiveManager()

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    def soft_delete(self):
        """Soft delete by setting is_active to False"""
        self.is_active = False
        self.save()

    def restore(self):
        """Restore soft deleted object"""
        self.is_active = True
        self.save()
