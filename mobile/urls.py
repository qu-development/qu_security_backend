from django.urls import path

from . import views

app_name = "mobile"

urlpatterns = [
    path("data/", views.MobileDataView.as_view(), name="mobile-data"),
]
