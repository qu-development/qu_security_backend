from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import BaseModel


class Shift(BaseModel):
    class Status(models.TextChoices):
        SCHEDULED = "scheduled", _("Scheduled")
        COMPLETED = "completed", _("Completed")
        VOIDED = "voided", _("Voided")

    guard = models.ForeignKey(
        "Guard",
        on_delete=models.CASCADE,
        related_name="shifts",
        verbose_name=_("Guard"),
    )
    property = models.ForeignKey(
        "Property",
        on_delete=models.CASCADE,
        related_name="shifts",
        verbose_name=_("Property"),
    )
    service = models.ForeignKey(
        "Service",
        on_delete=models.CASCADE,
        related_name="shifts",
        verbose_name=_("Service"),
        null=True,
        blank=True,
    )
    is_armed = models.BooleanField(default=False, verbose_name=_("Is Armed"))
    weapon = models.ForeignKey(
        "Weapon",
        on_delete=models.SET_NULL,
        related_name="shifts",
        verbose_name=_("Weapon"),
        null=True,
        blank=True,
    )
    planned_start_time = models.DateTimeField(
        verbose_name=_("Planned Start Time"), null=True, blank=True
    )
    planned_end_time = models.DateTimeField(
        verbose_name=_("Planned End Time"), null=True, blank=True
    )
    start_time = models.DateTimeField(
        verbose_name=_("Start Time"), null=True, blank=True
    )
    end_time = models.DateTimeField(verbose_name=_("End Time"), null=True, blank=True)
    hours_worked = models.PositiveIntegerField(
        default=0, validators=[MinValueValidator(0)], verbose_name=_("Hours Worked")
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED,
        verbose_name=_("Status"),
    )

    class Meta:
        verbose_name = _("Shift")
        verbose_name_plural = _("Shifts")

    def __str__(self):
        return _("Shift for %(guard)s at %(property)s") % {
            "guard": self.guard.user.username,
            "property": self.property.address,
        }
