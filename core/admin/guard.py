__all__ = ["GuardAdmin"]

import contextlib
import os
import tempfile

from django.contrib import admin, messages
from django.shortcuts import redirect, render
from django.urls import path, reverse
from django.utils.translation import gettext_lazy as _

from core.forms import GuardImportForm


class GuardAdmin(admin.ModelAdmin):
    change_list_template = "admin/core/guard/change_list.html"

    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "phone",
        "ssn",
    )

    list_display = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "phone",
        "address",
        "ssn",
        "is_armed",
        "created_at",
    )

    list_filter = (
        "is_armed",
        "created_at",
    )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "import-excel/",
                self.admin_site.admin_view(self.import_excel_view),
                name="guard_import_excel",
            ),
        ]
        return custom_urls + urls

    def import_excel_view(self, request):
        """Admin view for importing guards from Excel"""
        if request.method == "POST":
            form = GuardImportForm(request.POST, request.FILES)
            if form.is_valid():
                excel_file = form.cleaned_data["excel_file"]
                create_users = form.cleaned_data["create_users"]
                default_password = form.cleaned_data["default_password"]

                # Save uploaded file temporarily
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=".xlsx"
                ) as tmp_file:
                    for chunk in excel_file.chunks():
                        tmp_file.write(chunk)
                    tmp_file_path = tmp_file.name

                try:
                    # Import pandas here to avoid import errors if not installed
                    try:
                        from core.services.guard_import import GuardImportService
                    except ImportError:
                        messages.error(
                            request,
                            _(
                                "Required dependencies not installed. Please install pandas and openpyxl."
                            ),
                        )
                        return redirect("admin:core_guard_changelist")

                    # Process the file
                    service = GuardImportService()
                    results = service.process_excel_file(
                        tmp_file_path,
                        create_users=create_users,
                        default_password=default_password,
                    )

                    # Show results
                    if results["guards_created"] > 0:
                        messages.success(
                            request,
                            _(
                                f"Successfully created {results['guards_created']} guards."
                            ),
                        )

                    if results["warnings"]:
                        for warning in results["warnings"]:
                            messages.warning(request, warning)

                    if results["errors"]:
                        for error in results["errors"]:
                            messages.error(request, error)

                    # Additional summary message
                    summary_msg = _(
                        f"Import completed: {results['guards_created']} created, "
                        f"{results['rows_skipped']} skipped, "
                        f"{results['errors_count']} errors, "
                        f"{results['warnings_count']} warnings"
                    )
                    messages.info(request, summary_msg)

                    return redirect("admin:core_guard_changelist")

                finally:
                    # Clean up temporary file
                    with contextlib.suppress(OSError):
                        os.unlink(tmp_file_path)
        else:
            form = GuardImportForm()

        context = {
            "form": form,
            "title": _("Import Guards from Excel"),
            "opts": self.model._meta,
            "has_view_permission": True,
        }

        return render(request, "admin/core/guard/import_excel.html", context)

    def changelist_view(self, request, extra_context=None):
        """Add import button to changelist view"""
        extra_context = extra_context or {}
        extra_context["import_excel_url"] = reverse("admin:guard_import_excel")
        return super().changelist_view(request, extra_context=extra_context)
