__all__ = ["GuardAdmin"]

from django.contrib import admin


class GuardAdmin(admin.ModelAdmin):
    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "phone",
        "ssn",
    )
