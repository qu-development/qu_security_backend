from rest_framework import serializers

from ..models import Shift
from .guards import GuardSerializer
from .properties import PropertySerializer
from .services import ServiceSerializer


class ShiftSerializer(serializers.ModelSerializer):
    """Serializer for Shift model"""

    guard_details = GuardSerializer(source="guard", read_only=True)
    property_details = PropertySerializer(source="property", read_only=True)
    service_details = ServiceSerializer(source="service", read_only=True)

    class Meta:
        model = Shift
        fields = [
            "id",
            "guard",
            "guard_details",
            "property",
            "property_details",
            "service",
            "service_details",
            "start_time",
            "end_time",
            "hours_worked",
            "status",
        ]
        read_only_fields = ["id", "hours_worked"]

    def validate(self, attrs):
        """Ensure end_time is after start_time."""
        start = attrs.get("start_time")
        end = attrs.get("end_time")

        # For partial updates, fall back to instance values
        if self.instance is not None:
            start = start or getattr(self.instance, "start_time", None)
            end = end or getattr(self.instance, "end_time", None)

        if start and end and end <= start:
            raise serializers.ValidationError(
                {"end_time": "end_time must be after start_time"}
            )
        return attrs

    def _compute_hours(self, start, end) -> int:
        if not start or not end:
            return getattr(self.instance, "hours_worked", 0) if self.instance else 0
        seconds = (end - start).total_seconds()
        return int(max(0, seconds // 3600))

    def create(self, validated_data):
        hours = self._compute_hours(
            validated_data.get("start_time"), validated_data.get("end_time")
        )
        validated_data["hours_worked"] = hours
        return super().create(validated_data)

    def update(self, instance, validated_data):
        start = validated_data.get("start_time", instance.start_time)
        end = validated_data.get("end_time", instance.end_time)
        instance = super().update(instance, validated_data)
        instance.hours_worked = self._compute_hours(start, end)
        instance.save(update_fields=["hours_worked", "updated_at"])
        return instance
