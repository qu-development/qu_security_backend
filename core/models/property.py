from decimal import Decimal

from django.core.validators import MinValueValidator
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
    name = models.CharField(max_length=255, verbose_name=_("Name"), null=True)
    address = models.CharField(max_length=255, verbose_name=_("Address"))
    types_of_service = models.ManyToManyField(
        "PropertyTypeOfService",
        related_name="properties",
        verbose_name=_("Types of Service"),
    )
    monthly_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name=_("Monthly Rate"),
    )
    contract_start_date = models.DateField(
        verbose_name=_("Contract Start Date"), null=True
    )
    total_hours = models.PositiveIntegerField(
        default=0, validators=[MinValueValidator(0)], verbose_name=_("Total Hours")
    )

    class Meta:
        verbose_name = _("Property")
        verbose_name_plural = _("Properties")

    def __str__(self):
        return f"{self.address} - {self.owner.user.username}"
