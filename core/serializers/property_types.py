from rest_framework import serializers

from ..models import PropertyTypeOfService


class PropertyTypeOfServiceSerializer(serializers.ModelSerializer):
    """Serializer for PropertyTypeOfService model"""

    class Meta:
        model = PropertyTypeOfService
        fields = ["id", "name"]
        read_only_fields = ["id"]
