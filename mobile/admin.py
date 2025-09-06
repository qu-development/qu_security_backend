from django.contrib import admin

from .models import ApiKey

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
