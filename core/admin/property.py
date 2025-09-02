__all__ = ["PropertyAdmin"]
from django.contrib import admin


class PropertyAdmin(admin.ModelAdmin):
    list_display = (
        "owner__user__first_name",
        "name",
        "alias",
        "address",
        "get_services",
        "contract_start_date",
    )
    list_display_links = list_display

    @admin.display(description="Services")
    def get_services(self, obj):
        from core.models import Service

        services = Service.objects.filter(assigned_property=obj)
        return ", ".join([s.name for s in services])
