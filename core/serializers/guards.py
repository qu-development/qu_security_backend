import logging

from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from permissions.utils import PermissionManager

from ..models import Guard
from .users import UserSerializer

logger = logging.getLogger(__name__)


class GuardSerializer(serializers.ModelSerializer):
    """Serializer for Guard model"""

    user_details = UserSerializer(source="user", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    name = serializers.SerializerMethodField()

    class Meta:
        model = Guard
        fields = [
            "id",
            "user",
            "user_details",
            "first_name",
            "last_name",
            "name",
            "email",
            "birth_date",
            "phone",
            "ssn",
            "address",
        ]
        # user is read-only to avoid requiring it on update and to ignore any provided value
        read_only_fields = ["id", "user"]

    def get_name(self, obj):
        fn = (obj.user.first_name or "").strip()
        ln = (obj.user.last_name or "").strip()
        full = f"{fn} {ln}".strip()
        return full or obj.user.username


class GuardPropertiesShiftsSerializer(serializers.ModelSerializer):
    """Serializer for Guard with associated properties and shifts"""

    user_details = UserSerializer(source="user", read_only=True)
    name = serializers.SerializerMethodField()
    properties_and_shifts = serializers.SerializerMethodField()

    class Meta:
        model = Guard
        fields = [
            "id",
            "user_details",
            "name",
            "birth_date",
            "phone",
            "address",
            "properties_and_shifts",
        ]
        read_only_fields = ["id"]

    def get_name(self, obj):
        fn = (obj.user.first_name or "").strip()
        ln = (obj.user.last_name or "").strip()
        full = f"{fn} {ln}".strip()
        return full or obj.user.username

    def get_properties_and_shifts(self, obj):
        from .properties import PropertySerializer
        from .shifts import ShiftSerializer

        # Get all shifts for this guard
        shifts = obj.shifts.select_related("property", "service").all()

        # Group shifts by property
        properties_data = {}
        for shift in shifts:
            property_id = shift.property.id
            if property_id not in properties_data:
                properties_data[property_id] = {
                    "property": PropertySerializer(shift.property).data,
                    "shifts": [],
                }
            properties_data[property_id]["shifts"].append(ShiftSerializer(shift).data)

        return list(properties_data.values())


class GuardUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating Guard model including user fields"""

    # Allow updating user fields
    first_name = serializers.CharField(
        source="user.first_name", required=False, allow_blank=True
    )
    last_name = serializers.CharField(
        source="user.last_name", required=False, allow_blank=True
    )
    email = serializers.EmailField(source="user.email", required=False)

    # Read-only fields for response
    user_details = UserSerializer(source="user", read_only=True)
    name = serializers.SerializerMethodField()

    class Meta:
        model = Guard
        fields = [
            "id",
            "user",
            "user_details",
            "first_name",
            "last_name",
            "name",
            "email",
            "birth_date",
            "phone",
            "ssn",
            "address",
        ]
        read_only_fields = ["id", "user"]

    def get_name(self, obj):
        fn = (obj.user.first_name or "").strip()
        ln = (obj.user.last_name or "").strip()
        full = f"{fn} {ln}".strip()
        return full or obj.user.username

    def validate_email(self, value):
        """Validate email uniqueness excluding current user"""
        if value:
            user = self.instance.user if self.instance else None
            if (
                User.objects.filter(email__iexact=value)
                .exclude(id=user.id if user else None)
                .exists()
            ):
                raise serializers.ValidationError(_("Email is already in use."))
        return value

    def update(self, instance, validated_data):
        """Update both Guard and User fields"""
        # Extract user fields
        user_data = {}
        if "user" in validated_data:
            user_data = validated_data.pop("user")

        # Update user fields if provided
        if user_data:
            user = instance.user
            for attr, value in user_data.items():
                setattr(user, attr, value)
            user.save()

        # Update guard fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance


class GuardCreateSerializer(serializers.Serializer):
    """Serializer to create a Guard together with its User when needed.

    Supports two flows:
    - Provide an existing user via `user` (primary key), and we'll just create the Guard.
    - Omit `user` and provide `email` (+ optional names). We'll create the User
      with is_staff=False and is_superuser=False, then create the Guard and assign
      the 'guard' role/group.
    """

    # Existing user flow
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), required=False, allow_null=True
    )

    # New user flow
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False)

    # Guard fields
    phone = serializers.CharField(required=False, allow_blank=True)
    ssn = serializers.CharField(required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True)
    birth_date = serializers.DateField(required=False, allow_null=True)

    def validate(self, attrs):
        # Either a user must be provided or an email to create a user
        user = attrs.get("user")
        email = attrs.get("email")
        if not user and not email:
            raise serializers.ValidationError(
                {"email": _("Email is required when no user is provided.")}
            )

        # If user is provided, check if they already have a Guard profile
        if user and hasattr(user, "guard"):
            raise serializers.ValidationError(
                {"user": _("This user already has a Guard profile.")}
            )

        # If creating a new user, validate email uniqueness
        if not user and email and User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError({"email": _("Email is already in use.")})

        return attrs

    def _generate_unique_username(self, base: str) -> str:
        base = (base or "guard").strip()[:150]
        username = base or "guard"
        idx = 1
        while User.objects.filter(username=username).exists():
            suffix = str(idx)
            max_base_len = 150 - len(suffix)
            username = f"{base[:max_base_len]}{suffix}"
            idx += 1
        return username

    def create(self, validated_data):
        from django.db import IntegrityError, transaction

        request = self.context.get("request")
        acting_user = getattr(request, "user", None) if request else None

        user = validated_data.get("user")

        try:
            with transaction.atomic():
                if not user:
                    # Create the user first
                    email = validated_data.get("email")
                    first_name = validated_data.get("first_name", "")
                    last_name = validated_data.get("last_name", "")

                    local_part = (
                        email.split("@", 1)[0] if email and "@" in email else email
                    )
                    username = self._generate_unique_username(local_part)

                    # Double-check email uniqueness inside transaction
                    if User.objects.filter(email__iexact=email).exists():
                        raise serializers.ValidationError(
                            {"email": _("Email is already in use.")}
                        )

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

                # Double-check that user doesn't already have a Guard profile
                if hasattr(user, "guard"):
                    raise serializers.ValidationError(
                        {"user": _("This user already has a Guard profile.")}
                    )

                # Ensure groups exist and assign role/group 'guard' to the target user
                PermissionManager.setup_default_groups()
                if acting_user and getattr(acting_user, "is_authenticated", False):
                    PermissionManager.assign_user_role(
                        user, "guard", assigned_by=acting_user
                    )
                else:
                    # Fallback to self-assignment if no acting user
                    PermissionManager.assign_user_role(user, "guard", assigned_by=user)

                # Create Guard
                guard = Guard.objects.create(
                    user=user,
                    phone=validated_data.get("phone", ""),
                    ssn=validated_data.get("ssn", ""),
                    address=validated_data.get("address", ""),
                    birth_date=validated_data.get("birth_date"),
                )
                return guard

        except IntegrityError as e:
            logger.error(f"IntegrityError creating Guard: {str(e)}")
            if "core_guard_user_id_key" in str(e):
                raise serializers.ValidationError(
                    {"user": _("This user already has a Guard profile.")}
                )
            elif "auth_user_email" in str(e) or "email" in str(e).lower():
                raise serializers.ValidationError(
                    {"email": _("Email is already in use.")}
                )
            elif "auth_user_username" in str(e) or "username" in str(e).lower():
                raise serializers.ValidationError(
                    {
                        "email": _(
                            "Unable to generate unique username. Please try a different email."
                        )
                    }
                )
            else:
                raise serializers.ValidationError(
                    {
                        "non_field_errors": [
                            _(
                                "Database integrity error occurred. Please check your data."
                            )
                        ]
                    }
                )
        except Exception as e:
            logger.error(f"Unexpected error creating Guard: {str(e)}", exc_info=True)
            raise serializers.ValidationError(
                {
                    "non_field_errors": [
                        _("An unexpected error occurred: {}").format(str(e))
                    ]
                }
            )

    def to_representation(self, instance):
        return GuardSerializer(instance).data


class GuardDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for Guard model with user information"""

    user_details = UserSerializer(source="user", read_only=True)
    shifts_count = serializers.SerializerMethodField()
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    name = serializers.SerializerMethodField()

    class Meta:
        model = Guard
        fields = [
            "id",
            "user",
            "user_details",
            "first_name",
            "last_name",
            "name",
            "email",
            "phone",
            "ssn",
            "address",
            "birth_date",
            "shifts_count",
        ]
        read_only_fields = ["id"]

    def get_shifts_count(self, obj):
        return obj.shifts.count()

    def get_name(self, obj):
        fn = (obj.user.first_name or "").strip()
        ln = (obj.user.last_name or "").strip()
        full = f"{fn} {ln}".strip()
        return full or obj.user.username
