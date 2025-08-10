from decimal import Decimal

from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models


class Guard(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="guard")
    phone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.user.username} - Guard"


class Client(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="client")
    phone = models.CharField(max_length=20, blank=True)
    balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    def __str__(self):
        return f"{self.user.username} - Client"


class Property(models.Model):
    owner = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name="properties"
    )
    address = models.CharField(max_length=255)
    total_hours = models.PositiveIntegerField(
        default=0, validators=[MinValueValidator(0)]
    )

    def __str__(self):
        return f"{self.address} - {self.owner.username}"


class Shift(models.Model):
    guard = models.ForeignKey(Guard, on_delete=models.CASCADE, related_name="shifts")
    property = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name="shifts"
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    hours_worked = models.PositiveIntegerField(
        default=0, validators=[MinValueValidator(0)]
    )

    def __str__(self):
        return f"Shift for {self.guard.user.username} at {self.property.address}"


class Expense(models.Model):
    property = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name="expenses"
    )
    description = models.CharField(max_length=255)
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )

    def __str__(self):
        return f"Expense for {self.property.address} - {self.amount}"
