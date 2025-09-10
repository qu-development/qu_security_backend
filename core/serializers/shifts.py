from rest_framework import serializers

from ..models import Shift, Weapon
from .guards import GuardSerializer
from .properties import PropertySerializer
from .services import ServiceSerializer
from .weapons import WeaponSerializer


class ShiftSerializer(serializers.ModelSerializer):
    """Serializer for Shift model"""

    guard_details = GuardSerializer(source="guard", read_only=True)
    property_details = PropertySerializer(source="property", read_only=True)
    service_details = ServiceSerializer(source="service", read_only=True)
    weapon_details = serializers.SerializerMethodField()

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
            "planned_start_time",
            "planned_end_time",
            "start_time",
            "end_time",
            "hours_worked",
            "status",
            "is_armed",
            "weapon",
            "weapon_details",
        ]
        read_only_fields = ["id", "hours_worked"]

    def validate(self, attrs):
        """Ensure end times are after start times."""
        # Validate actual start/end times
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

        # Validate planned start/end times
        planned_start = attrs.get("planned_start_time")
        planned_end = attrs.get("planned_end_time")

        # For partial updates, fall back to instance values
        if self.instance is not None:
            planned_start = planned_start or getattr(
                self.instance, "planned_start_time", None
            )
            planned_end = planned_end or getattr(
                self.instance, "planned_end_time", None
            )

        if planned_start and planned_end and planned_end <= planned_start:
            raise serializers.ValidationError(
                {
                    "planned_end_time": "planned_end_time must be after planned_start_time"
                }
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

    def get_weapon_details(self, obj):
        """Return the weapon associated with the shift if specified, otherwise the first weapon of the guard if armed."""
        if obj.weapon:
            return WeaponSerializer(obj.weapon).data
        elif obj.guard and obj.is_armed:
            weapon = Weapon.objects.filter(guard=obj.guard).first()
            if weapon:
                return WeaponSerializer(weapon).data
        return None
