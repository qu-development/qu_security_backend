from rest_framework import serializers

from ..models import GuardPropertyTariff
from .guards import GuardSerializer
from .properties import PropertySerializer


class GuardPropertyTariffSerializer(serializers.ModelSerializer):
    """Serializer for GuardPropertyTariff model"""

    guard_details = GuardSerializer(source="guard", read_only=True)
    property_details = PropertySerializer(source="property", read_only=True)

    class Meta:
        model = GuardPropertyTariff
        fields = [
            "id",
            "guard",
            "guard_details",
            "property",
            "property_details",
            "rate",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
        # Disable automatic unique validators so we can handle conditional
        # uniqueness (only one active per pair) in the view logic and DB.
        validators = []
