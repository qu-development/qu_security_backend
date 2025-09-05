from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import BaseModel


class Property(BaseModel):
    owner = models.ForeignKey(
        "Client",
        on_delete=models.CASCADE,
        related_name="properties",
        verbose_name=_("Owner"),
    )
    description = models.TextField(verbose_name=_("Description"), null=True, blank=True)
    name = models.CharField(max_length=255, verbose_name=_("Name"), null=True)
    alias = models.CharField(
        max_length=255, verbose_name=_("Alias"), null=True, blank=True
    )
    address = models.CharField(max_length=255, verbose_name=_("Address"))

    class Meta:
        verbose_name = _("Property")
        verbose_name_plural = _("Properties")
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "alias"], name="unique_property_alias_per_owner"
            )
        ]

    def __str__(self):
        return f"{self.address} - {self.owner.user.username}"
