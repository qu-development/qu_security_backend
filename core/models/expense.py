from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import BaseModel


class Expense(BaseModel):
    property = models.ForeignKey(
        "Property",
        on_delete=models.CASCADE,
        related_name="expenses",
        verbose_name=_("Property"),
    )
    description = models.CharField(max_length=255, verbose_name=_("Description"))
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name=_("Amount"),
    )

    class Meta:
        verbose_name = _("Expense")
        verbose_name_plural = _("Expenses")

    def __str__(self):
        return _("Expense for %(property)s - %(amount)s") % {
            "property": self.property.address,
            "amount": self.amount,
        }
