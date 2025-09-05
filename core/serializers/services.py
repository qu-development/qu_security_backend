from rest_framework import serializers

from core.models import Service


class ServiceSerializer(serializers.ModelSerializer):
    """Serializer for Service model"""

    total_hours = serializers.ReadOnlyField()
    guard_name = serializers.CharField(
        source="guard.user.get_full_name", read_only=True
    )
    property_name = serializers.CharField(
        source="assigned_property.name", read_only=True
    )

    class Meta:
        model = Service
        fields = [
            "id",
            "name",
            "description",
            "guard",
            "guard_name",
            "assigned_property",
            "property_name",
            "rate",
            "monthly_budget",
            "contract_start_date",
            "total_hours",
            "created_at",
            "updated_at",
            "is_active",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "total_hours"]


class ServiceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Service instances"""

    class Meta:
        model = Service
        fields = [
            "name",
            "description",
            "guard",
            "assigned_property",
            "rate",
            "monthly_budget",
            "contract_start_date",
        ]


class ServiceUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating Service instances"""

    class Meta:
        model = Service
        fields = [
            "name",
            "description",
            "guard",
            "assigned_property",
            "rate",
            "monthly_budget",
            "is_active",
        ]
