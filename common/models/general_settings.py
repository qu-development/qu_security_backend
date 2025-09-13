from django.conf import settings
from django.core.cache import caches
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

    class Meta:
        verbose_name = _("General Settings")
        verbose_name_plural = _("General Settings")

    def __str__(self):  # pragma: no cover - simple representation
        return "General Settings"
