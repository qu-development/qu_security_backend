from django.db import models
from django.utils import timezone


class BaseModel(models.Model):
    """
    Abstract base model that provides common fields for all models.
    Includes automatic timestamp tracking and soft delete functionality.
    """

    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

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
