import secrets

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from common.models import BaseModel
from core.models import Guard


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


class GuardReport(BaseModel):
    """Report submitted by a guard from the mobile app.

    Includes an attached file (image/video/audio or any file), a note, the
    datetime the report was made, and optional geolocation (latitude/longitude).
    """

    guard = models.ForeignKey(
        Guard,
        on_delete=models.CASCADE,
        related_name="reports",
        verbose_name=_("Guard"),
    )
    file = models.FileField(
        _("file"),
        upload_to="guard_reports/%Y/%m/%d/",
        help_text=_("Attached file for this report."),
    )
    note = models.TextField(_("note"), blank=True)
    report_datetime = models.DateTimeField(
        _("report datetime"), default=timezone.now, db_index=True
    )
    latitude = models.DecimalField(
        _("latitude"),
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
        help_text=_("Latitude in decimal degrees (-90 to 90)."),
    )
    longitude = models.DecimalField(
        _("longitude"),
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
        help_text=_("Longitude in decimal degrees (-180 to 180)."),
    )

    class Meta:
        verbose_name = _("Guard Report")
        verbose_name_plural = _("Guard Reports")
        ordering = ("-report_datetime", "-created_at")

    def __str__(self):
        return f"{self.guard} @ {self.report_datetime:%Y-%m-%d %H:%M:%S}"
