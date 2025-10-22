"""
URLs for Excel report generation API
"""

from django.urls import path

from . import report_views

urlpatterns = [
    path(
        "generate-excel/",
        report_views.generate_excel_report,
        name="generate_excel_report",
    ),
    path("available-models/", report_views.available_models, name="available_models"),
]
