from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import BaseModel


class GuardPropertyTariff(BaseModel):
    guard = models.ForeignKey(
        "Guard",
        on_delete=models.CASCADE,
        related_name="property_tariffs",
        verbose_name=_("Guard"),
    )
    property = models.ForeignKey(
        "Property",
        on_delete=models.CASCADE,
        related_name="guard_tariffs",
        verbose_name=_("Property"),
    )
    rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name=_("Rate per Hour"),
    )

    class Meta:
        verbose_name = _("Guard Property Tariff")
        verbose_name_plural = _("Guard Property Tariffs")
        constraints = [
            models.UniqueConstraint(
                fields=["guard", "property"], name="unique_guard_property_tariff"
            )
        ]

    def __str__(self):
        return _("%(guard)s @ %(property)s: %(rate)s") % {
            "guard": self.guard.user.username,
            "property": self.property.address,
            "rate": self.rate,
        }
