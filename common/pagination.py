from __future__ import annotations

from django.conf import settings
from rest_framework.pagination import PageNumberPagination


class SettingsPageNumberPagination(PageNumberPagination):
    """
    DRF pagination class that reads the page size from the GeneralSettings
    singleton (api_page_size). Falls back to REST_FRAMEWORK["PAGE_SIZE"] or 20.
    """

    # Allow clients to override with ?page_size=...; otherwise use global setting
    page_size_query_param = "page_size"

    def get_page_size(self, request):  # type: ignore[override]
        # 1) Client override via query param
        qp_value = request.query_params.get(self.page_size_query_param)
        if qp_value is not None:
            try:
                qp_size = int(qp_value)
                if qp_size > 0:
                    return qp_size
            except (TypeError, ValueError):
                pass

        # 2) Fallback from settings, default to 20 if not present
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
