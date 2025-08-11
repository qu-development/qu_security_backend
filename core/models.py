from decimal import Decimal

from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import BaseModel


class Guard(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="guard")
    phone = models.CharField(max_length=20, blank=True, verbose_name=_("Phone"))

    class Meta:
        verbose_name = _("Guard")
        verbose_name_plural = _("Guards")

    def __str__(self):
        return f"{self.user.username} - {_('Guard')}"


class Client(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="client")
    phone = models.CharField(max_length=20, blank=True, verbose_name=_("Phone"))
    balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name=_("Balance"),
    )

    class Meta:
        verbose_name = _("Client")
        verbose_name_plural = _("Clients")

    def __str__(self):
        return f"{self.user.username} - {_('Client')}"


class Property(BaseModel):
    owner = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="properties",
        verbose_name=_("Owner"),
    )
    address = models.CharField(max_length=255, verbose_name=_("Address"))
    total_hours = models.PositiveIntegerField(
        default=0, validators=[MinValueValidator(0)], verbose_name=_("Total Hours")
    )

    class Meta:
        verbose_name = _("Property")
        verbose_name_plural = _("Properties")

    def __str__(self):
        return f"{self.address} - {self.owner.user.username}"


class Shift(BaseModel):
    guard = models.ForeignKey(
        Guard, on_delete=models.CASCADE, related_name="shifts", verbose_name=_("Guard")
    )
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name="shifts",
        verbose_name=_("Property"),
    )
    start_time = models.DateTimeField(verbose_name=_("Start Time"))
    end_time = models.DateTimeField(verbose_name=_("End Time"))
    hours_worked = models.PositiveIntegerField(
        default=0, validators=[MinValueValidator(0)], verbose_name=_("Hours Worked")
    )

    class Meta:
        verbose_name = _("Shift")
        verbose_name_plural = _("Shifts")

    def __str__(self):
        return _("Shift for %(guard)s at %(property)s") % {
            "guard": self.guard.user.username,
            "property": self.property.address,
        }


class Expense(BaseModel):
    property = models.ForeignKey(
        Property,
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
