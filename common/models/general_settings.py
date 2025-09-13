from django.conf import settings
from django.core.cache import cache, caches
from django.db import connection, models
from django.utils.translation import gettext_lazy as _
from solo.models import SingletonModel

from .base_model import BaseModel


class GeneralSettings(SingletonModel, BaseModel):
    """
    Singleton model to store application-wide configuration.

    Use via GeneralSettings.get_solo() to retrieve the single instance.
    """

    app_name = models.CharField(
        _("App Name"),
        max_length=100,
        help_text=_("Name of the application"),
        default="QU Security",
    )
    app_description = models.CharField(
        _("App Description"),
        max_length=255,
        help_text=_("Description of the application"),
        default="QU Security",
    )

    api_page_size = models.PositiveIntegerField(
        _("API Page Size"),
        default=20,
        help_text=_("Number of items per page across the API"),
    )

    @property
    def postgres_status(self):
        """Check the connectivity of the PostgreSQL database."""
        try:
            connection.ensure_connection()
            if connection.is_usable():
                return "Connected"
            return "Error: Connection not usable"
        except Exception as e:
            return f"Disconnected: {e}"

    @property
    def valkey_status(self):
        """Check the connectivity and type of the cache backend."""
        try:
            cache_backend = settings.CACHES["default"]["BACKEND"]
            if "redis" in cache_backend.lower() or "valkey" in cache_backend.lower():
                cache = caches["default"]
                try:
                    # For django-redis, we can use the cache's get_client method
                    if hasattr(cache, "get_client"):
                        client = cache.get_client()
                        if hasattr(client, "ping"):
                            if client.ping():
                                return "Connected (Valkey/Redis)"
                            return "Disconnected: Ping failed (Valkey/Redis)"

                    # Alternative approach: try to perform a simple cache operation
                    test_key = "connectivity_test"
                    cache.set(test_key, "test", 1)
                    if cache.get(test_key) == "test":
                        cache.delete(test_key)
                        return "Connected (Valkey/Redis)"
                    return "Disconnected: Cache operation failed (Valkey/Redis)"
                except Exception as conn_e:
                    return f"Disconnected: {conn_e} (Valkey/Redis)"
            elif "locmem" in cache_backend.lower():
                return "Active (In-Memory Cache)"
            else:
                return f"Active ({cache_backend})"
        except Exception as e:
            return f"Error determining cache status: {e}"

    @property
    def valkey_diagnostics(self):
        """Detailed diagnostic information for Valkey connection."""
        try:
            endpoint = getattr(settings, "VALKEY_ENDPOINT", "Not configured")
            port = getattr(settings, "VALKEY_PORT", "Not configured")
            ssl_enabled = getattr(settings, "VALKEY_SSL", "Not configured")

            return (
                f"Endpoint: {endpoint} | "
                f"Port: {port} | "
                f"SSL: {ssl_enabled} | "
                f"Backend: {settings.CACHES['default']['BACKEND']}"
            )
        except Exception as e:
            return f"Error getting diagnostics: {e}"

    @property
    def cache_test_info(self):
        """Display cache test information to verify Valkey is working."""
        try:
            test_message = cache.get("admin_test_message")
            if test_message:
                return f"✅ {test_message}"
            else:
                return "❌ No cache test data found - Cache may not be working"
        except Exception as e:
            return f"❌ Cache test failed: {e}"

    @property
    def cache_visit_count(self):
        """Display the number of admin visits stored in cache."""
        try:
            count = cache.get("admin_visit_count", 0)
            return f"Admin visits: {count}"
        except Exception as e:
            return f"Error getting visit count: {e}"

    @property
    def cache_last_access(self):
        """Display last admin access information from cache."""
        try:
            last_access = cache.get("admin_last_access")
            if last_access:
                return (
                    f"Last access: {last_access['timestamp']} | "
                    f"User: {last_access['user']} | "
                    f"IP: {last_access['ip']}"
                )
            else:
                return "No access data in cache"
        except Exception as e:
            return f"Error getting access data: {e}"

    class Meta:
        verbose_name = _("General Settings")
        verbose_name_plural = _("General Settings")

    def __str__(self):  # pragma: no cover - simple representation
        return "General Settings"
