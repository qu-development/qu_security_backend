from decimal import Decimal

from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.core.validators import DecimalValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import BaseModel


class Note(BaseModel):
    """
    Model for notes that can be related to any entity in the system.
    Allows tracking financial information (positive/negative amounts)
    and descriptions for various business entities.
    """

    name = models.CharField(
        max_length=255, verbose_name=_("Name"), help_text=_("Name or title of the note")
    )

    description = models.TextField(
        verbose_name=_("Description"),
        help_text=_("Detailed description of the note"),
        blank=True,
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Amount ($)"),
        help_text=_(
            "Financial amount - can be positive (income) or negative (expense)"
        ),
        validators=[DecimalValidator(max_digits=12, decimal_places=2)],
        null=True,
        blank=True,
    )

    # Array fields for optimized relations (store IDs as integer arrays)
    clients = ArrayField(
        models.PositiveIntegerField(),
        size=None,
        default=list,
        verbose_name=_("Clients"),
        help_text=_("Array of client IDs associated with this note"),
        blank=True,
    )

    properties = ArrayField(
        models.PositiveIntegerField(),
        size=None,
        default=list,
        verbose_name=_("Properties"),
        help_text=_("Array of property IDs associated with this note"),
        blank=True,
    )

    guards = ArrayField(
        models.PositiveIntegerField(),
        size=None,
        default=list,
        verbose_name=_("Guards"),
        help_text=_("Array of guard IDs associated with this note"),
        blank=True,
    )

    services = ArrayField(
        models.PositiveIntegerField(),
        size=None,
        default=list,
        verbose_name=_("Services"),
        help_text=_("Array of service IDs associated with this note"),
        blank=True,
    )

    shifts = ArrayField(
        models.PositiveIntegerField(),
        size=None,
        default=list,
        verbose_name=_("Shifts"),
        help_text=_("Array of shift IDs associated with this note"),
        blank=True,
    )

    weapons = ArrayField(
        models.PositiveIntegerField(),
        size=None,
        default=list,
        verbose_name=_("Weapons"),
        help_text=_("Array of weapon IDs associated with this note"),
        blank=True,
    )

    type_of_services = ArrayField(
        models.PositiveIntegerField(),
        size=None,
        default=list,
        verbose_name=_("Type of Services"),
        help_text=_("Array of property type of service IDs associated with this note"),
        blank=True,
    )

    viewed_by_ids = ArrayField(
        models.PositiveIntegerField(),
        size=None,
        default=list,
        verbose_name=_("Viewed by"),
        help_text=_("Array of user IDs who have viewed this note"),
        blank=True,
    )

    # User who created this note
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="created_notes",
        verbose_name=_("Created by"),
        null=True,
        blank=True,
        help_text=_("User who created this note"),
    )

    class Meta:
        verbose_name = _("Note")
        verbose_name_plural = _("Notes")
        ordering = ["-created_at"]  # Most recent first
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["created_by"]),
        ]

    def __str__(self):
        related_info = []
        amount_str = f"${self.amount:,.2f}" if self.amount else "$0.00"

        # Build related info string from arrays
        if self.clients:
            related_info.append(f"Clients: {len(self.clients)}")
        if self.properties:
            related_info.append(f"Properties: {len(self.properties)}")
        if self.guards:
            related_info.append(f"Guards: {len(self.guards)}")
        if self.services:
            related_info.append(f"Services: {len(self.services)}")
        if self.shifts:
            related_info.append(f"Shifts: {len(self.shifts)}")
        if self.weapons:
            related_info.append(f"Weapons: {len(self.weapons)}")
        if self.type_of_services:
            related_info.append(f"Type of Services: {len(self.type_of_services)}")

        related_str = " | ".join(related_info) if related_info else "No relations"
        return f"{self.name} ({amount_str}) - {related_str}"

    @property
    def is_income(self):
        """Returns True if amount is positive (income)"""
        return self.amount > 0

    @property
    def is_expense(self):
        """Returns True if amount is negative (expense)"""
        return self.amount < 0

    @property
    def amount_type(self):
        """Returns string describing the amount type"""
        if self.amount > 0:
            return _("Income")
        elif self.amount < 0:
            return _("Expense")
        else:
            return _("Neutral")

    def get_related_entities(self):
        """Returns a list of all related entity IDs organized by type"""
        entities = {}

        if self.clients:
            entities["clients"] = self.clients
        if self.properties:
            entities["properties"] = self.properties
        if self.guards:
            entities["guards"] = self.guards
        if self.services:
            entities["services"] = self.services
        if self.shifts:
            entities["shifts"] = self.shifts
        if self.weapons:
            entities["weapons"] = self.weapons
        if self.type_of_services:
            entities["type_of_services"] = self.type_of_services
        if self.viewed_by_ids:
            entities["viewed_by_ids"] = self.viewed_by_ids

        return entities
