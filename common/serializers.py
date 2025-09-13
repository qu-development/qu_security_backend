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
            "valkey_diagnostics",
            "cache_test_info",
            "cache_visit_count",
            "cache_last_access",
        ]
        read_only_fields = fields
