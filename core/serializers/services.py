from rest_framework import serializers

from core.models import Service


class ServiceSerializer(serializers.ModelSerializer):
    """Serializer for Service model"""

    total_hours = serializers.IntegerField(
        source="scheduled_total_hours", read_only=True
    )
    guard_name = serializers.CharField(
        source="guard.user.get_full_name", read_only=True
    )
    property_name = serializers.CharField(
        source="assigned_property.name", read_only=True
    )
    weekly_display = serializers.SerializerMethodField(read_only=True)

    def get_weekly_display(self, obj):
        """Return formatted string of weekly days"""
        return obj.get_weekly_days_display()

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
            "schedule",
            "recurrent",
            "start_time",
            "end_time",
            "weekly",
            "weekly_display",
            "start_date",
            "end_date",
            "total_hours",
            "created_at",
            "updated_at",
            "is_active",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "total_hours"]


class ServiceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Service instances"""

    def validate_weekly(self, value):
        """Validate weekly field contains valid weekdays"""
        if value:
            invalid_days = [day for day in value if day not in Service.ALL_WEEKDAYS]
            if invalid_days:
                raise serializers.ValidationError(
                    f"Invalid weekdays: {', '.join(invalid_days)}. "
                    f"Valid options are: {', '.join(Service.ALL_WEEKDAYS)}"
                )
        return value

    def validate(self, data):
        """Custom validation for Service creation"""
        # Ensure start_date is before end_date if both are provided
        start_date = data.get("start_date")
        end_date = data.get("end_date")

        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError(
                {"end_date": "End date must be after start date."}
            )

        return data

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
            "schedule",
            "recurrent",
            "start_time",
            "end_time",
            "weekly",
            "start_date",
            "end_date",
            "scheduled_total_hours",
            "is_active",
        ]


class ServiceUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating Service instances"""

    def validate_weekly(self, value):
        """Validate weekly field contains valid weekdays"""
        if value:
            invalid_days = [day for day in value if day not in Service.ALL_WEEKDAYS]
            if invalid_days:
                raise serializers.ValidationError(
                    f"Invalid weekdays: {', '.join(invalid_days)}. "
                    f"Valid options are: {', '.join(Service.ALL_WEEKDAYS)}"
                )
        return value

    def validate(self, data):
        """Custom validation for Service updates"""
        # Ensure start_date is before end_date if both are provided
        start_date = data.get("start_date")
        end_date = data.get("end_date")

        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError(
                {"end_date": "End date must be after start date."}
            )

        return data

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
            "schedule",
            "recurrent",
            "start_time",
            "end_time",
            "weekly",
            "start_date",
            "end_date",
            "scheduled_total_hours",
            "is_active",
        ]
