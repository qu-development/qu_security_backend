from django.contrib import admin
from solo.admin import SingletonModelAdmin

from .models import GeneralSettings


@admin.register(GeneralSettings)
class GeneralSettingsAdmin(SingletonModelAdmin):
    pass
