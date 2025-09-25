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
    def cache_status(self):
        """Check the connectivity and type of the current cache backend."""
        try:
            cache_backend = settings.CACHES["default"]["BACKEND"]
            cache = caches["default"]
            # Perform a simple set/get
            test_key = "connectivity_test"
            cache.set(test_key, "test", 1)
            if cache.get(test_key) == "test":
                cache.delete(test_key)
                if "memcached" in cache_backend.lower():
                    return "Connected (Memcached)"
                elif "locmem" in cache_backend.lower():
                    return "Active (In-Memory Cache)"
                else:
                    return f"Connected ({cache_backend})"
            return f"Disconnected: Cache set/get failed ({cache_backend})"
        except Exception as e:
            return f"Error determining cache status: {e}"

    @property
    def cache_diagnostics(self):
        """Diagnostic information for the active cache backend (Memcached/LocMem)."""
        try:
            endpoint = getattr(settings, "MEMCACHED_ENDPOINT", "Not configured")
            port = getattr(settings, "MEMCACHED_PORT", "Not configured")
            backend = settings.CACHES["default"]["BACKEND"]

            return f"Endpoint: {endpoint} | Port: {port} | Backend: {backend}"
        except Exception as e:
            return f"Error getting diagnostics: {e}"

    @property
    def cache_viewer(self):
        """Display selected keys and values in the cache (best-effort).

        Note: Memcached does not support listing keys, so we check common
        patterns used by the application (e.g., guards_rts:{id}).
        """
        try:
            cache = caches["default"]
            cache_data = {}

            # Backends typically don't support listing; test common patterns
            for i in range(1, 501):  # Check first 500 guard IDs
                test_key = f"guards_rts:{i}"
                try:
                    value = cache.get(test_key)
                    if value is not None:
                        if isinstance(value, dict | list | tuple):
                            cache_data[test_key] = json.dumps(value, indent=2)
                        else:
                            cache_data[test_key] = str(value)
                except Exception:
                    print(f"Error accessing cache key {test_key}")

            # Display results
            if not cache_data:
                return format_html(
                    "<p><em>No cache keys found or cache is empty</em></p>"
                )

            # Format for HTML display
            html_content = "<div style='max-height: 400px; overflow-y: auto; font-family: monospace; font-size: 12px;'>"
            html_content += (
                f"<p><strong>Total Keys Found:</strong> {len(cache_data)}</p>"
            )

            for key, value in cache_data.items():
                html_content += "<div style='margin-bottom: 15px; padding: 10px; background-color: #f8f9fa; border-left: 3px solid #007cba;'>"
                html_content += (
                    f"<strong style='color: #007cba;'>Key:</strong> {key}<br>"
                )
                html_content += "<strong style='color: #28a745;'>Value:</strong><br>"
                html_content += f"<pre style='white-space: pre-wrap; word-wrap: break-word; margin: 5px 0; padding: 5px; background-color: #ffffff; border: 1px solid #dee2e6;'>{value}</pre>"
                html_content += "</div>"

            html_content += "</div>"
            return format_html(html_content)

        except Exception as e:
            return f"Error accessing cache: {e}"

    class Meta:
        verbose_name = _("General Settings")
        verbose_name_plural = _("General Settings")

    def __str__(self):  # pragma: no cover - simple representation
        return "General Settings"
