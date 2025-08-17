from rest_framework import serializers

from ..models import Expense
from .properties import PropertySerializer


class ExpenseSerializer(serializers.ModelSerializer):
    """Serializer for Expense model"""

    property_details = PropertySerializer(source="property", read_only=True)

    class Meta:
        model = Expense
        fields = ["id", "property", "property_details", "description", "amount"]
        read_only_fields = ["id"]
