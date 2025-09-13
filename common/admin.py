from django.contrib import admin
from django.core.cache import cache
from django.utils import timezone
from solo.admin import SingletonModelAdmin

from .models import GeneralSettings


@admin.register(GeneralSettings)
class GeneralSettingsAdmin(SingletonModelAdmin):
    readonly_fields = (
        "postgres_status",
        "valkey_status",
        "valkey_diagnostics",
        "cache_test_info",
        "cache_visit_count",
        "cache_last_access",
    )
    fieldsets = (
        (None, {"fields": ("app_name", "app_description", "api_page_size")}),
        ("Connectivity Status", {"fields": ("postgres_status", "valkey_status")}),
        ("Valkey Diagnostics", {"fields": ("valkey_diagnostics",)}),
        (
            "Cache Testing",
            {"fields": ("cache_test_info", "cache_visit_count", "cache_last_access")},
        ),
    )

    def changelist_view(self, request, extra_context=None):
        """Override to perform cache operations on each admin visit."""
        self._perform_cache_test(request)
        return super().changelist_view(request, extra_context)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        """Override to perform cache operations on each admin visit."""
        self._perform_cache_test(request)
        return super().change_view(request, object_id, form_url, extra_context)

    def _perform_cache_test(self, request):
        """Perform cache operations to test Valkey connectivity."""
        try:
            now = timezone.now()
            user = (
                request.user.username if request.user.is_authenticated else "Anonymous"
            )

            # Increment visit counter
            current_count = cache.get("admin_visit_count", 0)
            cache.set("admin_visit_count", current_count + 1, timeout=3600)

            # Save last access info
            cache.set(
                "admin_last_access",
                {
                    "timestamp": now.isoformat(),
                    "user": user,
                    "ip": self._get_client_ip(request),
                },
                timeout=3600,
            )

            # Save a test message
            cache.set(
                "admin_test_message", f"Cache test successful at {now}", timeout=3600
            )

        except Exception:
            # If cache operations fail, we'll see it in the cache_test_info property
            print("Cache test failed")

    def _get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip
