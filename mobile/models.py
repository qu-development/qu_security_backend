import secrets

from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import BaseModel


class ApiKey(BaseModel):
    """Model to store API keys for mobile clients."""

    name = models.CharField(
        _("name"),
        max_length=100,
        unique=True,
        help_text=_("A human-readable name for the API key."),
    )
    key = models.CharField(
        _("key"),
        max_length=64,
        unique=True,
        db_index=True,
        help_text=_("The unique API key."),
    )
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_("Uncheck this to disable the API key without deleting it."),
    )

    class Meta:
        verbose_name = _("API Key")
        verbose_name_plural = _("API Keys")
        ordering = ("-created_at",)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.key:
            # Generate a secure, URL-safe random key
            self.key = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)
