from decimal import Decimal

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
    )

    # Relations to all core models (all optional/nullable)
    client = models.ForeignKey(
        "Client",
        on_delete=models.SET_NULL,
        related_name="notes",
        verbose_name=_("Client"),
        null=True,
        blank=True,
        help_text=_("Associated client"),
    )

    property_obj = models.ForeignKey(
        "Property",
        on_delete=models.SET_NULL,
        related_name="notes",
        verbose_name=_("Property"),
        null=True,
        blank=True,
        help_text=_("Associated property"),
    )

    guard = models.ForeignKey(
        "Guard",
        on_delete=models.SET_NULL,
        related_name="notes",
        verbose_name=_("Guard"),
        null=True,
        blank=True,
        help_text=_("Associated guard"),
    )

    service = models.ForeignKey(
        "Service",
        on_delete=models.SET_NULL,
        related_name="notes",
        verbose_name=_("Service"),
        null=True,
        blank=True,
        help_text=_("Associated service"),
    )

    shift = models.ForeignKey(
        "Shift",
        on_delete=models.SET_NULL,
        related_name="notes",
        verbose_name=_("Shift"),
        null=True,
        blank=True,
        help_text=_("Associated shift"),
    )

    expense = models.ForeignKey(
        "Expense",
        on_delete=models.SET_NULL,
        related_name="notes",
        verbose_name=_("Expense"),
        null=True,
        blank=True,
        help_text=_("Associated expense"),
    )

    weapon = models.ForeignKey(
        "Weapon",
        on_delete=models.SET_NULL,
        related_name="notes",
        verbose_name=_("Weapon"),
        null=True,
        blank=True,
        help_text=_("Associated weapon"),
    )

    guard_property_tariff = models.ForeignKey(
        "GuardPropertyTariff",
        on_delete=models.SET_NULL,
        related_name="notes",
        verbose_name=_("Guard Property Tariff"),
        null=True,
        blank=True,
        help_text=_("Associated guard property tariff"),
    )

    property_type_of_service = models.ForeignKey(
        "PropertyTypeOfService",
        on_delete=models.SET_NULL,
        related_name="notes",
        verbose_name=_("Property Type Of Service"),
        null=True,
        blank=True,
        help_text=_("Associated property type of service"),
    )

    class Meta:
        verbose_name = _("Note")
        verbose_name_plural = _("Notes")
        ordering = ["-created_at"]  # Most recent first
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["amount"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["client", "property_obj"]),
        ]

    def __str__(self):
        related_info = []

        # Build related info string
        if self.client:
            related_info.append(f"Client: {self.client}")
        if self.property_obj:
            related_info.append(f"Property: {self.property_obj}")
        if self.guard:
            related_info.append(f"Guard: {self.guard}")
        if self.service:
            related_info.append(f"Service: {self.service}")
        if self.shift:
            related_info.append(f"Shift: {self.shift}")
        if self.expense:
            related_info.append(f"Expense: {self.expense}")
        if self.weapon:
            related_info.append(f"Weapon: {self.weapon}")
        if self.guard_property_tariff:
            related_info.append(f"Tariff: {self.guard_property_tariff}")
        if self.property_type_of_service:
            related_info.append(f"Property Type: {self.property_type_of_service}")

        related_str = " | ".join(related_info) if related_info else "No relations"
        amount_str = f"${self.amount:,.2f}" if self.amount else "$0.00"

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
        """Returns a list of all related entities"""
        entities = []
        relations = [
            ("client", self.client),
            ("property", self.property_obj),
            ("guard", self.guard),
            ("service", self.service),
            ("shift", self.shift),
            ("expense", self.expense),
            ("weapon", self.weapon),
            ("guard_property_tariff", self.guard_property_tariff),
            ("property_type_of_service", self.property_type_of_service),
        ]

        for relation_name, relation_obj in relations:
            if relation_obj:
                entities.append(
                    {
                        "type": relation_name,
                        "id": relation_obj.id,
                        "str": str(relation_obj),
                    }
                )

        return entities
