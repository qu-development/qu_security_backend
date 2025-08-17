from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from ..models import Client


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
