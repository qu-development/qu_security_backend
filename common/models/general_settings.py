from django.db import models
from django.utils.translation import gettext_lazy as _
from solo.models import SingletonModel

from .base_model import BaseModel


class GeneralSettings(SingletonModel, BaseModel):
    """
    Singleton model to store application-wide configuration.

    Use via GeneralSettings.get_solo() to retrieve the single instance.
    """

    app_name = models.CharField(
        _("App Name"),
        max_length=100,
        help_text=_("Name of the application"),
        default="QU Security",
    )
    app_description = models.CharField(
        _("App Description"),
        max_length=255,
        help_text=_("Description of the application"),
        default="QU Security",
    )

    api_page_size = models.PositiveIntegerField(
        _("API Page Size"),
        default=20,
        help_text=_("Number of items per page across the API"),
    )

    class Meta:
        verbose_name = _("General Settings")
        verbose_name_plural = _("General Settings")

    def __str__(self):  # pragma: no cover - simple representation
        return "General Settings"
