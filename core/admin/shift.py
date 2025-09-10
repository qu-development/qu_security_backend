from django.contrib import admin


class ShiftAdmin(admin.ModelAdmin):
    """
    Admin configuration for Shift model.
    """

    list_display = (
        "id",
        "guard",
        "property",
        "service",
        "planned_start_time",
        "planned_end_time",
        "start_time",
        "end_time",
        "hours_worked",
        "status",
        "is_armed",
        "weapon",
    )
    list_filter = ("status", "is_armed", "guard", "property", "service")
    search_fields = ("guard__user__username", "property__address")
    readonly_fields = ("hours_worked",)
    fieldsets = (
        (None, {"fields": ("guard", "property", "service", "is_armed", "weapon")}),
        ("Planning", {"fields": ("planned_start_time", "planned_end_time")}),
        ("Execution", {"fields": ("start_time", "end_time", "hours_worked", "status")}),
    )
