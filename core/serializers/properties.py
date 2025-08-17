from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from ..models import Property, PropertyTypeOfService
from .clients import ClientSerializer
from .property_types import PropertyTypeOfServiceSerializer


class PropertySerializer(serializers.ModelSerializer):
    """Serializer for Property model"""

    owner_details = ClientSerializer(source="owner", read_only=True)
    types_of_service = serializers.PrimaryKeyRelatedField(
        queryset=PropertyTypeOfService.objects.all(), many=True, required=False
    )

    class Meta:
        model = Property
        fields = [
            "id",
            "owner",
            "owner_details",
            "name",
            "alias",
            "address",
            "types_of_service",
            "monthly_rate",
            "contract_start_date",
            "total_hours",
        ]

        read_only_fields = ["id", "owner"]

    def validate(self, attrs):
        alias_value = attrs.get("alias", serializers.empty)
        # Normalize blank alias to None so it doesn't trip unique constraint
        if alias_value is not serializers.empty:
            normalized = (alias_value or "").strip()
            if not normalized:
                attrs["alias"] = None
            else:
                # Determine owner: instance owner on update, request.user.client on create
                owner = None
                if getattr(self, "instance", None) is not None:
                    owner = getattr(self.instance, "owner", None)
                else:
                    request = (
                        self.context.get("request")
                        if hasattr(self, "context")
                        else None
                    )
                    owner = (
                        getattr(getattr(request, "user", None), "client", None)
                        if request
                        else None
                    )

                if owner is not None:
                    qs = Property.objects.filter(owner=owner, alias=normalized)
                    if getattr(self, "instance", None) is not None:
                        qs = qs.exclude(pk=self.instance.pk)
                    if qs.exists():
                        raise serializers.ValidationError(
                            {"alias": _("Alias must be unique for this owner.")}
                        )
                # Keep normalized value
                attrs["alias"] = normalized

        return super().validate(attrs)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Represent types_of_service as detailed objects under the same key
        data["types_of_service"] = PropertyTypeOfServiceSerializer(
            instance.types_of_service.filter(is_active=True), many=True
        ).data
        return data


class PropertyDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for Property model with owner information"""

    owner_details = ClientSerializer(source="owner", read_only=True)
    shifts_count = serializers.SerializerMethodField()
    expenses_count = serializers.SerializerMethodField()
    total_expenses_amount = serializers.SerializerMethodField()
    types_of_service = serializers.PrimaryKeyRelatedField(
        queryset=PropertyTypeOfService.objects.all(), many=True, required=False
    )

    class Meta:
        model = Property
        fields = [
            "id",
            "owner",
            "owner_details",
            "name",
            "alias",
            "address",
            "types_of_service",
            "monthly_rate",
            "contract_start_date",
            "total_hours",
            "shifts_count",
            "expenses_count",
            "total_expenses_amount",
        ]
        read_only_fields = ["id", "owner"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Represent types_of_service as detailed objects under the same key
        data["types_of_service"] = PropertyTypeOfServiceSerializer(
            instance.types_of_service.filter(is_active=True), many=True
        ).data
        return data

    def get_shifts_count(self, obj):
        return obj.shifts.count()

    def get_expenses_count(self, obj):
        return obj.expenses.count()

    def get_total_expenses_amount(self, obj):
        from decimal import Decimal

        total = Decimal("0.00")
        for expense in obj.expenses.all():
            total += expense.amount
        return total
