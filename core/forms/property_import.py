from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class PropertyImportForm(forms.Form):
    """Form for importing properties from Excel file"""

    excel_file = forms.FileField(
        label=_("Excel File"),
        help_text=_(
            "Upload an Excel file (.xlsx) with property data. Required columns: PROPERTY NAME, SOBRE NOMBRE, PROPERTY OWNER"
        ),
        widget=forms.FileInput(
            attrs={"accept": ".xlsx,.xls", "class": "form-control-file"}
        ),
    )

    create_clients = forms.BooleanField(
        label=_("Create Client Accounts"),
        help_text=_(
            "Create Django user and client accounts for each property owner. Username will be generated from owner name."
        ),
        initial=True,
        required=False,
    )

    def clean_excel_file(self):
        file = self.cleaned_data.get("excel_file")
        if file:
            if not file.name.endswith((".xlsx", ".xls")):
                raise forms.ValidationError(
                    _("Please upload a valid Excel file (.xlsx or .xls)")
                )

            # Check file size (limit to 10MB)
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError(_("File size cannot exceed 10MB"))

        return file

    def clean(self):
        cleaned_data = super().clean()
        # Use password from settings for created client accounts
        cleaned_data["default_password"] = settings.GUARD_DEFAULT_PASSWORD
        return cleaned_data
