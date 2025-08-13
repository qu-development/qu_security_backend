from django.urls import path

from .api import GeneralSettingsRetrieveView

app_name = "common"

urlpatterns = [
    path(
        "general-settings/",
        GeneralSettingsRetrieveView.as_view(),
        name="general-settings",
    ),
]
