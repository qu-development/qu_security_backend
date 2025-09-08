from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views
from .api.guard_reports import GuardReportViewSet

app_name = "mobile"

router = DefaultRouter()
router.register(r"guard-reports", GuardReportViewSet, basename="guard-report")

urlpatterns = [
    path("data/", views.MobileDataView.as_view(), name="mobile-data"),
    path("", include(router.urls)),
]
