from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import BaseModel

from .guard import Guard


class Weapon(BaseModel):
    guard = models.ForeignKey(
        Guard, on_delete=models.CASCADE, related_name="weapons", verbose_name=_("Guard")
    )
    serial_number = models.CharField(max_length=100, verbose_name=_("Serial Number"))
    model = models.CharField(max_length=100, verbose_name=_("Model"))

    class Meta:
        verbose_name = _("Weapon")
        verbose_name_plural = _("Weapons")
        unique_together = [
            "guard",
            "serial_number",
        ]  # Un guardia no puede tener dos armas con el mismo número de serie

    def __str__(self):
        return f"{self.guard.user.username} - {self.model} ({self.serial_number})"
