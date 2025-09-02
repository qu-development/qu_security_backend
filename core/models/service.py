from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import BaseModel


class Service(BaseModel):
    """Model for services that can be assigned to properties"""
    
    name = models.CharField(max_length=255, verbose_name=_("Name"))
    description = models.TextField(verbose_name=_("Description"), blank=True)
    
    # Guard assigned to this service (nullable - service can exist without guard)
    guard = models.ForeignKey(
        "Guard",
        on_delete=models.SET_NULL,
        related_name="services",
        verbose_name=_("Guard"),
        null=True,
        blank=True
    )
    
    # Property assigned to this service (nullable - service can exist without property)
    assigned_property = models.ForeignKey(
        "Property",
        on_delete=models.SET_NULL,
        related_name="assigned_services",
        verbose_name=_("Property"),
        null=True,
        blank=True
    )
    
    # Rate per hour for this service
    rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name=_("Rate per Hour ($)")
    )
    
    # Monthly budget for this service (previously monthly_rate)
    monthly_budget = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name=_("Monthly Budget ($)")
    )
    
    # Hours will be calculated based on completed shifts
    # This is a computed field that will be calculated dynamically
    @property
    def total_hours(self):
        """Calculate total hours based on completed shifts for this service"""
        from .shift import Shift
        return self.shifts.filter(status=Shift.Status.COMPLETED).aggregate(
            total=models.Sum('hours_worked')
        )['total'] or 0
    
    class Meta:
        verbose_name = _("Service")
        verbose_name_plural = _("Services")
        ordering = ["name"]
    
    def __str__(self):
        return self.name