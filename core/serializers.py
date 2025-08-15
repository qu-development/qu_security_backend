from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from .models import (
    Client,
    Expense,
    Guard,
    GuardPropertyTariff,
    Property,
    PropertyTypeOfService,
    Shift,
)


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model with all fields"""

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "is_staff",
            "is_superuser",
            "date_joined",
            "last_login",
        ]
        read_only_fields = ["id", "date_joined", "last_login"]


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new user"""

    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "password",
            "password_confirm",
            "is_active",
            "is_staff",
        ]

    def validate(self, attrs):
        """Validate that passwords match"""
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(_("Passwords don't match"))
        return attrs

    def create(self, validated_data):
        """Create a new user with encrypted password"""
        validated_data.pop("password_confirm")
        user = User.objects.create_user(**validated_data)
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user information"""

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "is_active", "is_staff"]


class LoginSerializer(serializers.Serializer):
    """Serializer for user login"""

    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")

        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError(_("Invalid credentials"))
            if not user.is_active:
                raise serializers.ValidationError(_("User account is disabled"))
            attrs["user"] = user
        else:
            raise serializers.ValidationError(_("Must include username and password"))

        return attrs


class GuardSerializer(serializers.ModelSerializer):
    """Serializer for Guard model"""

    user_details = UserSerializer(source="user", read_only=True)

    class Meta:
        model = Guard
        fields = ["id", "user", "user_details", "phone", "ssn", "address"]
        read_only_fields = ["id"]


class GuardDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for Guard model with user information"""

    user_details = UserSerializer(source="user", read_only=True)
    shifts_count = serializers.SerializerMethodField()

    class Meta:
        model = Guard
        fields = [
            "id",
            "user",
            "user_details",
            "phone",
            "ssn",
            "address",
            "shifts_count",
        ]
        read_only_fields = ["id"]

    def get_shifts_count(self, obj):
        return obj.shifts.count()


class ClientSerializer(serializers.ModelSerializer):
    """Serializer for Client model"""

    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Client
        fields = [
            "id",
            "user",
            "first_name",
            "last_name",
            "email",
            "phone",
            "balance",
            "created_at",
            "updated_at",
            "is_active",
        ]
        read_only_fields = ["id", "balance", "created_at", "updated_at", "is_active"]


class ClientDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for Client model with user information"""

    properties_count = serializers.SerializerMethodField()
    total_expenses = serializers.SerializerMethodField()
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Client
        fields = [
            "id",
            "user",
            "first_name",
            "last_name",
            "email",
            "phone",
            "balance",
            "properties_count",
            "total_expenses",
            "created_at",
            "updated_at",
            "is_active",
        ]
        read_only_fields = ["id", "balance", "created_at", "updated_at", "is_active"]

    def get_properties_count(self, obj):
        return obj.properties.count()

    def get_total_expenses(self, obj):
        from decimal import Decimal

        total = Decimal("0.00")
        for property_obj in obj.properties.all():
            for expense in property_obj.expenses.all():
                total += expense.amount
        return total


class ClientCreateSerializer(serializers.Serializer):
    """Serializer for creating a new Client along with its User"""

    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField()
    phone = serializers.CharField(required=False, allow_blank=True)

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(_("Email is already in use."))
        return value

    def _generate_unique_username(self, base: str) -> str:
        base = base or "client"
        base = base.strip()[:150]
        username = base
        idx = 1
        while User.objects.filter(username=username).exists():
            suffix = str(idx)
            max_base_len = 150 - len(suffix)
            username = f"{base[:max_base_len]}{suffix}"
            idx += 1
        return username

    def create(self, validated_data):
        email = validated_data.get("email")
        first_name = validated_data.get("first_name", "")
        last_name = validated_data.get("last_name", "")
        phone = validated_data.get("phone", "")

        local_part = email.split("@", 1)[0] if email and "@" in email else email
        username = self._generate_unique_username(local_part)

        user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            is_staff=False,
            is_superuser=False,
        )
        user.set_unusable_password()
        user.save()

        client = Client.objects.create(user=user, phone=phone)
        return client

    def to_representation(self, instance):
        # Reuse the standard client representation after creation
        return ClientSerializer(instance).data


class ClientUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a Client and its related User fields"""

    first_name = serializers.CharField(
        source="user.first_name", required=False, allow_blank=True
    )
    last_name = serializers.CharField(
        source="user.last_name", required=False, allow_blank=True
    )
    email = serializers.EmailField(source="user.email", required=False)

    class Meta:
        model = Client
        fields = ["first_name", "last_name", "email", "phone"]

    def validate(self, attrs):
        user_data = attrs.get("user", {})
        email = user_data.get("email")
        if email:
            qs = User.objects.filter(email__iexact=email)
            if self.instance and self.instance.user_id:
                qs = qs.exclude(pk=self.instance.user_id)
            if qs.exists():
                raise serializers.ValidationError(
                    {"email": _("Email is already in use.")}
                )
        return attrs

    def update(self, instance, validated_data):
        user_data = validated_data.pop("user", {})

        # Update client fields
        phone = validated_data.get("phone", serializers.empty)
        if phone is not serializers.empty:
            instance.phone = phone
        instance.save()

        # Update related user fields
        user = instance.user
        for field in ("first_name", "last_name", "email"):
            if field in user_data:
                setattr(user, field, user_data[field])
        user.save()
        return instance

    def to_representation(self, instance):
        # Return the standard client representation
        return ClientSerializer(instance).data


class PropertyTypeOfServiceSerializer(serializers.ModelSerializer):
    """Serializer for PropertyTypeOfService model"""

    class Meta:
        model = PropertyTypeOfService
        fields = ["id", "name"]
        read_only_fields = ["id"]


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


class ShiftSerializer(serializers.ModelSerializer):
    """Serializer for Shift model"""

    guard_details = GuardSerializer(source="guard", read_only=True)
    property_details = PropertySerializer(source="property", read_only=True)

    class Meta:
        model = Shift
        fields = [
            "id",
            "guard",
            "guard_details",
            "property",
            "property_details",
            "start_time",
            "end_time",
            "hours_worked",
        ]
        read_only_fields = ["id"]


class ExpenseSerializer(serializers.ModelSerializer):
    """Serializer for Expense model"""

    property_details = PropertySerializer(source="property", read_only=True)

    class Meta:
        model = Expense
        fields = ["id", "property", "property_details", "description", "amount"]
        read_only_fields = ["id"]


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
        ]
        read_only_fields = ["id"]
