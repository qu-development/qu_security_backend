from django.contrib import admin

from .models import ApiKey, GuardReport

# Register your models here.


@admin.register(ApiKey)
class ApiKeyAdmin(admin.ModelAdmin):
    """Admin interface for managing API Keys."""

    list_display = ("name", "key", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name",)
    readonly_fields = ("key", "created_at", "updated_at")

    fieldsets = (
        (None, {"fields": ("name", "is_active")}),
        ("Key Details", {"fields": ("key",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    def get_readonly_fields(self, request, obj=None):
        """Make the key field readonly after creation."""
        if obj:
            return self.readonly_fields + ("name",)
        return self.readonly_fields


@admin.register(GuardReport)
class GuardReportAdmin(admin.ModelAdmin):
    """Admin interface for Guard reports."""

    list_display = (
        "id",
        "guard",
        "report_datetime",
        "is_active",
        "created_at",
    )
    list_filter = ("is_active", "report_datetime")
    search_fields = (
        "guard__user__username",
        "guard__user__first_name",
        "guard__user__last_name",
        "note",
    )
    raw_id_fields = ("guard",)
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("guard", "file", "note", "report_datetime", "is_active")}),
        ("Location", {"fields": ("latitude", "longitude")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )
