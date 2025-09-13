import json

from django.conf import settings
from django.core.cache import caches
from django.db import connection, models
from django.utils.html import format_html
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
    def cache_viewer(self):
        """Display all keys and values in the Valkey cache."""
        try:
            cache = caches["default"]

            # Try to get all keys using django-redis specific method
            if hasattr(cache, "get_client"):
                client = cache.get_client()
                if hasattr(client, "keys"):
                    keys = client.keys("*")
                    if not keys:
                        return format_html("<p><em>No keys found in cache</em></p>")

                    cache_data = {}
                    for key in keys:
                        # Decode key if it's bytes
                        if isinstance(key, bytes):
                            key = key.decode("utf-8")

                        try:
                            value = cache.get(key)
                            # Format the value for display
                            if isinstance(value, dict | list | tuple):
                                cache_data[key] = json.dumps(value, indent=2)
                            else:
                                cache_data[key] = str(value)
                        except Exception as e:
                            cache_data[key] = f"Error retrieving value: {e}"

                    # Format for HTML display
                    html_content = "<div style='max-height: 400px; overflow-y: auto; font-family: monospace; font-size: 12px;'>"
                    html_content += (
                        f"<p><strong>Total Keys:</strong> {len(cache_data)}</p>"
                    )

                    for key, value in cache_data.items():
                        html_content += "<div style='margin-bottom: 15px; padding: 10px; background-color: #f8f9fa; border-left: 3px solid #007cba;'>"
                        html_content += (
                            f"<strong style='color: #007cba;'>Key:</strong> {key}<br>"
                        )
                        html_content += (
                            "<strong style='color: #28a745;'>Value:</strong><br>"
                        )
                        html_content += f"<pre style='white-space: pre-wrap; word-wrap: break-word; margin: 5px 0; padding: 5px; background-color: #ffffff; border: 1px solid #dee2e6;'>{value}</pre>"
                        html_content += "</div>"

                    html_content += "</div>"
                    return format_html(html_content)
                else:
                    return "Cache client doesn't support key listing"
            else:
                return "Cache backend doesn't support direct key access"

        except Exception as e:
            return f"Error accessing cache: {e}"

    class Meta:
        verbose_name = _("General Settings")
        verbose_name_plural = _("General Settings")

    def __str__(self):  # pragma: no cover - simple representation
        return "General Settings"
