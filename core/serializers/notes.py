from decimal import Decimal

from rest_framework import serializers

from core.models import Note


class NoteSerializer(serializers.ModelSerializer):
    """Serializer for Note model with array relations"""

    # Display computed properties
    amount_type = serializers.ReadOnlyField()
    is_income = serializers.ReadOnlyField()
    is_expense = serializers.ReadOnlyField()

    # Display created_by name
    created_by_name = serializers.SerializerMethodField()

    # Related entities summary
    related_entities = serializers.SerializerMethodField()

    class Meta:
        model = Note
        fields = [
            "id",
            "name",
            "description",
            "amount",
            "amount_type",
            "is_income",
            "is_expense",
            # Array relation fields
            "clients",
            "properties",
            "guards",
            "services",
            "shifts",
            "weapons",
            "type_of_services",
            "viewed_by_ids",
            # User who created
            "created_by",
            "created_by_name",
            # Computed fields
            "related_entities",
            # BaseModel fields
            "created_at",
            "updated_at",
            "is_active",
        ]

        read_only_fields = [
            "id",
            "amount_type",
            "is_income",
            "is_expense",
            "created_by",
            "created_by_name",
            "related_entities",
            "created_at",
            "updated_at",
        ]

    def get_created_by_name(self, obj):
        """Get created by user display name"""
        if obj.created_by:
            return f"{obj.created_by.get_full_name() or obj.created_by.username}"
        return None

    def get_related_entities(self, obj):
        """Get summary of all related entities"""
        return obj.get_related_entities()

    def validate_amount(self, value):
        """Validate amount field"""
        if value is None:
            return Decimal("0.00")
        return value

    def validate(self, attrs):
        """Custom validation"""
        # Ensure at least name is provided
        if not attrs.get("name", "").strip():
            raise serializers.ValidationError({"name": "This field cannot be empty."})

        # Validate that array fields are actually lists
        array_fields = [
            "clients",
            "properties",
            "guards",
            "services",
            "shifts",
            "weapons",
            "type_of_services",
            "viewed_by_ids",
        ]

        for field_name in array_fields:
            if field_name in attrs and attrs[field_name] is not None:
                if not isinstance(attrs[field_name], list):
                    raise serializers.ValidationError(
                        {field_name: "This field must be a list of integers."}
                    )
                # Validate that all items in the list are positive integers
                for item in attrs[field_name]:
                    if not isinstance(item, int) or item <= 0:
                        raise serializers.ValidationError(
                            {field_name: "All items must be positive integers."}
                        )

        return attrs


class NoteCreateSerializer(serializers.ModelSerializer):
    """Simplified serializer for creating notes"""

    class Meta:
        model = Note
        fields = [
            "id",
            "name",
            "description",
            "amount",
            "clients",
            "properties",
            "guards",
            "services",
            "shifts",
            "weapons",
            "type_of_services",
            "viewed_by_ids",
            "created_by",
        ]

        read_only_fields = ["id", "created_by"]

    def validate_amount(self, value):
        """Validate amount field"""
        if value is None:
            return Decimal("0.00")
        return value

    def validate(self, attrs):
        """Custom validation for create"""
        # Ensure at least name is provided
        if not attrs.get("name", "").strip():
            raise serializers.ValidationError({"name": "This field cannot be empty."})

        # Validate array fields
        array_fields = [
            "clients",
            "properties",
            "guards",
            "services",
            "shifts",
            "weapons",
            "type_of_services",
            "viewed_by_ids",
        ]

        for field_name in array_fields:
            if field_name in attrs and attrs[field_name] is not None:
                if not isinstance(attrs[field_name], list):
                    raise serializers.ValidationError(
                        {field_name: "This field must be a list of integers."}
                    )
                # Validate that all items in the list are positive integers
                for item in attrs[field_name]:
                    if not isinstance(item, int) or item <= 0:
                        raise serializers.ValidationError(
                            {field_name: "All items must be positive integers."}
                        )

        return attrs


class NoteUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating notes"""

    class Meta:
        model = Note
        fields = [
            "name",
            "description",
            "amount",
            "clients",
            "properties",
            "guards",
            "services",
            "shifts",
            "weapons",
            "type_of_services",
            "viewed_by_ids",
            "is_active",
        ]

    def validate_amount(self, value):
        """Validate amount field"""
        if value is None:
            return Decimal("0.00")
        return value

    def validate(self, attrs):
        """Custom validation for update"""
        # Validate array fields
        array_fields = [
            "clients",
            "properties",
            "guards",
            "services",
            "shifts",
            "weapons",
            "type_of_services",
            "viewed_by_ids",
        ]

        for field_name in array_fields:
            if field_name in attrs and attrs[field_name] is not None:
                if not isinstance(attrs[field_name], list):
                    raise serializers.ValidationError(
                        {field_name: "This field must be a list of integers."}
                    )
                # Validate that all items in the list are positive integers
                for item in attrs[field_name]:
                    if not isinstance(item, int) or item <= 0:
                        raise serializers.ValidationError(
                            {field_name: "All items must be positive integers."}
                        )

        return attrs


class NoteSummarySerializer(serializers.ModelSerializer):
    """Lightweight serializer for note summaries"""

    amount_type = serializers.ReadOnlyField()
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Note
        fields = [
            "id",
            "name",
            "amount",
            "amount_type",
            "created_by",
            "created_by_name",
            "created_at",
        ]

    def get_created_by_name(self, obj):
        """Get created by user display name"""
        if obj.created_by:
            return f"{obj.created_by.get_full_name() or obj.created_by.username}"
        return None
