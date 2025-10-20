__all__ = ["PropertyAdmin"]

import contextlib
import os
import tempfile

from django.contrib import admin, messages
from django.shortcuts import redirect, render
from django.urls import path
from django.utils.translation import gettext_lazy as _

from core.forms import PropertyImportForm
from core.services.property_import import PropertyImportService


class PropertyAdmin(admin.ModelAdmin):
    change_list_template = "admin/core/property/change_list.html"

    list_display = (
        "owner__user__first_name",
        "name",
        "alias",
        "address",
        "get_services",
    )
    list_display_links = list_display

    @admin.display(description="Services")
    def get_services(self, obj):
        from core.models import Service

        services = Service.objects.filter(assigned_property=obj)
        return ", ".join([s.name for s in services])

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path(
                "import-excel/",
                self.import_excel_view,
                name="core_property_import_excel",
            ),
        ]
        return my_urls + urls

    def import_excel_view(self, request):
        if request.method == "POST":
            form = PropertyImportForm(request.POST, request.FILES)
            if form.is_valid():
                excel_file = form.cleaned_data["excel_file"]
                create_clients = form.cleaned_data["create_clients"]
                default_password = form.cleaned_data["default_password"]

                # Save uploaded file temporarily
                tmp_file_path = None
                try:
                    with tempfile.NamedTemporaryFile(
                        delete=False, suffix=".xlsx"
                    ) as tmp_file:
                        for chunk in excel_file.chunks():
                            tmp_file.write(chunk)
                        tmp_file_path = tmp_file.name

                    # Process the Excel file
                    import_service = PropertyImportService()
                    results = import_service.process_excel_file(
                        tmp_file_path, create_clients, default_password
                    )

                    # Display results
                    if results["properties_created"] > 0:
                        messages.success(
                            request,
                            _(
                                f"Successfully imported {results['properties_created']} properties!"
                            ),
                        )

                    if results["errors_count"] > 0:
                        for error in results["errors"]:
                            messages.error(request, error)

                    if results["warnings_count"] > 0:
                        for warning in results["warnings"]:
                            messages.warning(request, warning)

                    if results["rows_skipped"] > 0:
                        messages.info(
                            request,
                            _(
                                f"{results['rows_skipped']} rows were skipped due to missing data."
                            ),
                        )

                    return redirect("admin:core_property_changelist")

                finally:
                    # Clean up temporary file
                    with contextlib.suppress(OSError):
                        os.unlink(tmp_file_path)
        else:
            form = PropertyImportForm()

        context = {
            "form": form,
            "title": _("Import Properties from Excel"),
            "opts": self.model._meta,
            "has_view_permission": True,
        }

        return render(request, "admin/core/property/import_excel.html", context)
