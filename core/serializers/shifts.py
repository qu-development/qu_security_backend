from rest_framework import serializers

from ..models import Shift
from .guards import GuardSerializer
from .properties import PropertySerializer


class ShiftSerializer(serializers.ModelSerializer):
    """Serializer for Shift model"""

    guard_details = GuardSerializer(source="guard", read_only=True)
    property_details = PropertySerializer(source="property", read_only=True)

    class Meta:
        model = Shift
        fields = [
            "id",
            "guard",
            "guard_details",
            "property",
            "property_details",
            "start_time",
            "end_time",
            "hours_worked",
        ]
        read_only_fields = ["id"]
