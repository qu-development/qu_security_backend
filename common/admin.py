from django.contrib import admin
from solo.admin import SingletonModelAdmin

from .models import GeneralSettings


@admin.register(GeneralSettings)
class GeneralSettingsAdmin(SingletonModelAdmin):
    readonly_fields = (
        "postgres_status",
        "valkey_status",
        "valkey_diagnostics",
        "cache_viewer",
    )
    fieldsets = (
        (None, {"fields": ("app_name", "app_description", "api_page_size")}),
        ("Connectivity Status", {"fields": ("postgres_status", "valkey_status")}),
        ("Valkey Diagnostics", {"fields": ("valkey_diagnostics",)}),
        ("Cache Contents", {"fields": ("cache_viewer",)}),
    )
