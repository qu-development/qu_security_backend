from decimal import Decimal

from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import BaseModel


class Service(BaseModel):
    """Model for services that can be assigned to properties"""

    # Days of the week constants for weekly field
    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"
    SATURDAY = "Saturday"
    SUNDAY = "Sunday"

    WEEKDAYS_CHOICES = [
        (MONDAY, _("Monday")),
        (TUESDAY, _("Tuesday")),
        (WEDNESDAY, _("Wednesday")),
        (THURSDAY, _("Thursday")),
        (FRIDAY, _("Friday")),
        (SATURDAY, _("Saturday")),
        (SUNDAY, _("Sunday")),
    ]

    # All weekdays for easy reference
    ALL_WEEKDAYS = [MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY]

    name = models.CharField(max_length=255, verbose_name=_("Name"))
    description = models.TextField(verbose_name=_("Description"), blank=True)

    # Guard assigned to this service (nullable - service can exist without guard)
    guard = models.ForeignKey(
        "Guard",
        on_delete=models.SET_NULL,
        related_name="services",
        verbose_name=_("Guard"),
        null=True,
        blank=True,
    )

    # Property assigned to this service (nullable - service can exist without property)
    assigned_property = models.ForeignKey(
        "Property",
        on_delete=models.SET_NULL,
        related_name="assigned_services",
        verbose_name=_("Property"),
        null=True,
        blank=True,
    )

    # Rate per hour for this service
    rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name=_("Rate per Hour ($)"),
        null=True,
        blank=True,
    )

    # Monthly budget for this service (previously monthly_rate)
    monthly_budget = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name=_("Monthly Budget ($)"),
        null=True,
        blank=True,
    )

    # Contract start date for this service
    contract_start_date = models.DateField(
        verbose_name=_("Contract Start Date"), null=True, blank=True
    )

    # Schedule dates for this service
    schedule = ArrayField(
        models.DateField(),
        verbose_name=_("Schedule Dates"),
        null=True,
        blank=True,
        help_text=_("Dates when this service is scheduled to be performed"),
    )

    # Start and end time for this service
    start_time = models.TimeField(
        verbose_name=_("Start Time"),
        null=True,
        blank=True,
        help_text=_("Time when this service starts each day"),
    )
    end_time = models.TimeField(
        verbose_name=_("End Time"),
        null=True,
        blank=True,
        help_text=_("Time when this service ends each day"),
    )

    # Whether this service is recurrent
    recurrent = models.BooleanField(
        verbose_name=_("Recurrent"),
        default=False,
        help_text=_("Whether this service is performed on a recurring basis"),
    )

    # Weekly schedule - days of the week when service is performed
    weekly = ArrayField(
        models.CharField(max_length=10, choices=WEEKDAYS_CHOICES),
        verbose_name=_("Weekly Schedule"),
        null=True,
        blank=True,
        default=list,
        help_text=_("Days of the week when this service is performed"),
    )

    # Service start date
    start_date = models.DateField(
        verbose_name=_("Start Date"),
        null=True,
        blank=True,
        help_text=_("Date when this service begins (MM/DD/YYYY format)"),
    )

    # Service end date
    end_date = models.DateField(
        verbose_name=_("End Date"),
        null=True,
        blank=True,
        help_text=_("Date when this service ends (MM/DD/YYYY format)"),
    )

    # Scheduled total hours for this service
    scheduled_total_hours = models.PositiveIntegerField(
        verbose_name=_("Scheduled Total Hours"),
        default=0,
        help_text=_("Total scheduled hours for this service"),
    )

    # Hours will be calculated based on completed shifts
    # This is a computed field that will be calculated dynamically
    @property
    def total_hours(self):
        """Calculate total hours based on completed shifts for this service"""
        from .shift import Shift

        return (
            self.shifts.filter(status=Shift.Status.COMPLETED).aggregate(
                total=models.Sum("hours_worked")
            )["total"]
            or 0
        )

    def get_weekly_days_display(self):
        """Return a formatted string of weekly days"""
        if not self.weekly:
            return _("No days selected")
        return ", ".join(self.weekly)

    def is_scheduled_for_day(self, day_name):
        """Check if service is scheduled for a specific day"""
        return day_name in (self.weekly or [])

    def clean(self):
        """Validate weekly field contains only valid weekdays"""
        super().clean()
        if self.weekly:
            invalid_days = [day for day in self.weekly if day not in self.ALL_WEEKDAYS]
            if invalid_days:
                raise ValidationError(
                    {
                        "weekly": _(
                            "Invalid weekdays: {}. Valid options are: {}"
                        ).format(", ".join(invalid_days), ", ".join(self.ALL_WEEKDAYS))
                    }
                )

    class Meta:
        verbose_name = _("Service")
        verbose_name_plural = _("Services")
        ordering = ["name"]

    def __str__(self):
        return self.name
