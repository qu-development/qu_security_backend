from rest_framework import serializers

from ..models import Weapon
from .guards import GuardSerializer


class WeaponSerializer(serializers.ModelSerializer):
    """Serializer for Weapon model"""

    guard_details = GuardSerializer(source="guard", read_only=True)

    class Meta:
        model = Weapon
        fields = [
            "id",
            "guard",
            "guard_details",
            "serial_number",
            "model",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class WeaponCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Weapon instances"""

    class Meta:
        model = Weapon
        fields = [
            "guard",
            "serial_number",
            "model",
        ]

    def validate(self, data):
        """Validate that the guard doesn't already have a weapon with the same serial number"""
        guard = data.get("guard")
        serial_number = data.get("serial_number")

        if (
            guard
            and serial_number
            and Weapon.objects.filter(guard=guard, serial_number=serial_number).exists()
        ):
            raise serializers.ValidationError(
                "This guard already has a weapon with this serial number."
            )

        return data


class WeaponUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating Weapon instances"""

    class Meta:
        model = Weapon
        fields = [
            "serial_number",
            "model",
        ]

    def validate_serial_number(self, value):
        """Validate that the guard doesn't already have another weapon with this serial number"""
        guard = self.instance.guard

        if (
            Weapon.objects.filter(guard=guard, serial_number=value)
            .exclude(id=self.instance.id)
            .exists()
        ):
            raise serializers.ValidationError(
                "This guard already has another weapon with this serial number."
            )

        return value
