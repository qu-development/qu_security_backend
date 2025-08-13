__all__ = ["PropertyAdmin"]
from django.contrib import admin


class PropertyAdmin(admin.ModelAdmin):
    list_display = (
        "owner__user__first_name",
        "monthly_rate",
        "name",
        "address",
        "get_types_of_service",
        "contract_start_date",
        "total_hours",
    )
    list_display_links = list_display
    filter_horizontal = ("types_of_service",)

    @admin.display(description="Types of Service")
    def get_types_of_service(self, obj):
        return ", ".join([t.name for t in obj.types_of_service.all()])
