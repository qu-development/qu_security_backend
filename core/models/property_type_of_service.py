from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import BaseModel


class PropertyTypeOfService(BaseModel):
    name = models.CharField(max_length=255, verbose_name=_("Name"))

    class Meta:
        verbose_name = _("Property Type of Service")
        verbose_name_plural = _("Property Type of Services")

    def __str__(self):
        return self.name
