from decimal import Decimal

from rest_framework import serializers

from core.models import Note


class NoteSerializer(serializers.ModelSerializer):
    """Serializer for Note model with all relations"""

    # Use PrimaryKeyRelatedField to show IDs instead of full objects
    client = serializers.PrimaryKeyRelatedField(read_only=True)
    property_obj = serializers.PrimaryKeyRelatedField(read_only=True)
    guard = serializers.PrimaryKeyRelatedField(read_only=True)
    service = serializers.PrimaryKeyRelatedField(read_only=True)
    shift = serializers.PrimaryKeyRelatedField(read_only=True)
    expense = serializers.PrimaryKeyRelatedField(read_only=True)
    weapon = serializers.PrimaryKeyRelatedField(read_only=True)
    guard_property_tariff = serializers.PrimaryKeyRelatedField(read_only=True)
    property_type_of_service = serializers.PrimaryKeyRelatedField(read_only=True)

    # Display related entity names
    client_name = serializers.SerializerMethodField()
    property_name = serializers.SerializerMethodField()
    guard_name = serializers.SerializerMethodField()
    service_name = serializers.SerializerMethodField()
    shift_name = serializers.SerializerMethodField()
    expense_name = serializers.SerializerMethodField()
    weapon_name = serializers.SerializerMethodField()
    guard_property_tariff_name = serializers.SerializerMethodField()
    property_type_of_service_name = serializers.SerializerMethodField()

    # Display computed properties
    amount_type = serializers.ReadOnlyField()
    is_income = serializers.ReadOnlyField()
    is_expense = serializers.ReadOnlyField()

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
            # Relation IDs
            "client",
            "property_obj",
            "guard",
            "service",
            "shift",
            "expense",
            "weapon",
            "guard_property_tariff",
            "property_type_of_service",
            # Relation names (read-only)
            "client_name",
            "property_name",
            "guard_name",
            "service_name",
            "shift_name",
            "expense_name",
            "weapon_name",
            "guard_property_tariff_name",
            "property_type_of_service_name",
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
            "client_name",
            "property_name",
            "guard_name",
            "service_name",
            "shift_name",
            "expense_name",
            "weapon_name",
            "guard_property_tariff_name",
            "property_type_of_service_name",
            "related_entities",
            "created_at",
            "updated_at",
        ]

    def get_client_name(self, obj):
        """Get client display name"""
        return str(obj.client) if obj.client else None

    def get_property_name(self, obj):
        """Get property display name"""
        return str(obj.property_obj) if obj.property_obj else None

    def get_guard_name(self, obj):
        """Get guard display name"""
        return str(obj.guard) if obj.guard else None

    def get_service_name(self, obj):
        """Get service display name"""
        return str(obj.service) if obj.service else None

    def get_shift_name(self, obj):
        """Get shift display name"""
        return str(obj.shift) if obj.shift else None

    def get_expense_name(self, obj):
        """Get expense display name"""
        return str(obj.expense) if obj.expense else None

    def get_weapon_name(self, obj):
        """Get weapon display name"""
        return str(obj.weapon) if obj.weapon else None

    def get_guard_property_tariff_name(self, obj):
        """Get guard property tariff display name"""
        return str(obj.guard_property_tariff) if obj.guard_property_tariff else None

    def get_property_type_of_service_name(self, obj):
        """Get property type of service display name"""
        return (
            str(obj.property_type_of_service) if obj.property_type_of_service else None
        )

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
            "client",
            "property_obj",
            "guard",
            "service",
            "shift",
            "expense",
            "weapon",
            "guard_property_tariff",
            "property_type_of_service",
        ]

        read_only_fields = ["id"]

    def validate_amount(self, value):
        """Validate amount field"""
        if value is None:
            return Decimal("0.00")
        return value


class NoteUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating notes"""

    class Meta:
        model = Note
        fields = [
            "name",
            "description",
            "amount",
            "client",
            "property_obj",
            "guard",
            "service",
            "shift",
            "expense",
            "weapon",
            "guard_property_tariff",
            "property_type_of_service",
            "is_active",
        ]

    def validate_amount(self, value):
        """Validate amount field"""
        if value is None:
            return Decimal("0.00")
        return value


class NoteSummarySerializer(serializers.ModelSerializer):
    """Lightweight serializer for note summaries"""

    amount_type = serializers.ReadOnlyField()

    class Meta:
        model = Note
        fields = [
            "id",
            "name",
            "amount",
            "amount_type",
            "created_at",
        ]
