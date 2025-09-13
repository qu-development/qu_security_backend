from rest_framework import serializers

from .models import GeneralSettings


class GeneralSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneralSettings
        fields = [
            "app_name",
            "app_description",
            "api_page_size",
            "postgres_status",
            "valkey_status",
        ]
        read_only_fields = fields
