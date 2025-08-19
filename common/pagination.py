from __future__ import annotations

from django.conf import settings
from rest_framework.pagination import PageNumberPagination


class SettingsPageNumberPagination(PageNumberPagination):
    """
    DRF pagination class that reads the page size from the GeneralSettings
    singleton (api_page_size). Falls back to REST_FRAMEWORK["PAGE_SIZE"] or 20.
    """

    # Keep client from overriding page size via query param; enforce global value
    page_size_query_param = None

    def get_page_size(self, request):  # type: ignore[override]
        # Fallback from settings, default to 20 if not present
        fallback = getattr(settings, "REST_FRAMEWORK", {}).get("PAGE_SIZE", 20)

        try:
            # Import here to avoid any app-loading timing issues
            from common.models import GeneralSettings

            gs = GeneralSettings.get_solo()
            size = getattr(gs, "api_page_size", None)
            if isinstance(size, int) and size > 0:
                return size
        except Exception:
            # On any error (e.g., during initial migrate), use fallback
            return fallback

        return fallback
