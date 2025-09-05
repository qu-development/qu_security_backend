__all__ = ["ServiceAdmin"]
from django.contrib import admin


class ServiceAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "description",
        "guard",
        "assigned_property",
        "rate",
        "monthly_budget",
        "contract_start_date",
    )
    list_display_links = list_display
