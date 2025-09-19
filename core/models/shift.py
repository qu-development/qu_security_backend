from decimal import Decimal

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

    planned_hours_worked = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0.00)],
        verbose_name=_("Planned Hours Worked"),
        help_text=_("Calculated hours between planned start and end times"),
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED,
        verbose_name=_("Status"),
    )

    def save(self, *args, **kwargs):
        """Override save to calculate planned_hours_worked and hours_worked before saving"""

        from django.utils import timezone

        # Calculate planned hours if both times are provided
        if self.planned_start_time and self.planned_end_time:
            start_time = self.planned_start_time
            end_time = self.planned_end_time

            # Convert strings to datetime objects if necessary
            if isinstance(start_time, str):
                start_time = timezone.datetime.fromisoformat(
                    start_time.replace("Z", "+00:00")
                )
            if isinstance(end_time, str):
                end_time = timezone.datetime.fromisoformat(
                    end_time.replace("Z", "+00:00")
                )

            time_diff = end_time - start_time
            hours = time_diff.total_seconds() / 3600
            self.planned_hours_worked = Decimal(str(round(max(hours, 0.0), 2)))
        else:
            self.planned_hours_worked = Decimal("0.00")

        # Calculate actual hours worked if both start_time and end_time are provided
        if self.start_time and self.end_time and self.status == self.Status.COMPLETED:
            start_time = self.start_time
            end_time = self.end_time

            # Convert strings to datetime objects if necessary
            if isinstance(start_time, str):
                start_time = timezone.datetime.fromisoformat(
                    start_time.replace("Z", "+00:00")
                )
            if isinstance(end_time, str):
                end_time = timezone.datetime.fromisoformat(
                    end_time.replace("Z", "+00:00")
                )

            time_diff = end_time - start_time
            hours = time_diff.total_seconds() / 3600
            self.hours_worked = int(round(max(hours, 0.0)))
        elif self.status != self.Status.COMPLETED:
            # Reset hours_worked if status is not completed
            self.hours_worked = 0

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _("Shift")
        verbose_name_plural = _("Shifts")

    def __str__(self):
        return _("Shift for %(guard)s at %(property)s") % {
            "guard": self.guard.user.username,
            "property": self.property.address,
        }
