"""
API views for generating Excel reports from model data
"""

import io
from typing import Any

import pandas as pd
from django.contrib.auth.models import User
from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import Client, Guard, Property, Shift


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def generate_excel_report(request):
    """
    Generate Excel report with data from specified models

    Expected JSON payload:
    {
        "models": ["guard", "property", "shift"],
        "filename": "report_2025_10_22.xlsx"  # Optional
    }

    Returns: Excel file download
    """
    try:
        data = request.data
        model_names = data.get("models", [])
        filename = data.get("filename", "report.xlsx")

        if not model_names:
            return Response(
                {"error": "No models specified"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Validate model names
        available_models = {
            "guard": Guard,
            "property": Property,
            "shift": Shift,
            "client": Client,
            "user": User,
        }

        invalid_models = [name for name in model_names if name not in available_models]
        if invalid_models:
            return Response(
                {
                    "error": f"Invalid models: {invalid_models}",
                    "available_models": list(available_models.keys()),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Generate Excel with multiple sheets
        excel_buffer = io.BytesIO()

        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
            for model_name in model_names:
                model_class = available_models[model_name]

                # Get data for this model
                model_data = _get_model_data(model_class, model_name)

                if model_data:
                    # Create DataFrame
                    df = pd.DataFrame(model_data)

                    # Write to Excel sheet
                    sheet_name = model_name.capitalize()
                    df.to_excel(writer, sheet_name=sheet_name, index=False)

                    # Auto-adjust column widths
                    worksheet = writer.sheets[sheet_name]
                    for column in worksheet.columns:
                        max_length = 0
                        column_letter = column[0].column_letter
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except (TypeError, AttributeError):
                                # Handle cases where cell.value might be None or have issues
                                continue
                        adjusted_width = min(max_length + 2, 50)
                        worksheet.column_dimensions[
                            column_letter
                        ].width = adjusted_width

        excel_buffer.seek(0)

        # Ensure filename has .xlsx extension
        if not filename.endswith(".xlsx"):
            filename = f"{filename}.xlsx"

        # Create HTTP response with Excel file
        response = HttpResponse(
            excel_buffer.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        response["Content-Length"] = len(excel_buffer.getvalue())

        # Additional headers to ensure proper Excel download
        response["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response["Pragma"] = "no-cache"
        response["Expires"] = "0"

        return response

    except Exception as e:
        return Response(
            {"error": f"Error generating report: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def _get_model_data(model_class, model_name: str) -> list[dict[str, Any]]:
    """Extract data from model based on model type"""

    if model_name == "guard":
        return _get_guard_data()
    elif model_name == "property":
        return _get_property_data()
    elif model_name == "shift":
        return _get_shift_data()
    elif model_name == "client":
        return _get_client_data()
    elif model_name == "user":
        return _get_user_data()
    else:
        return []


def _get_guard_data() -> list[dict[str, Any]]:
    """Get Guard data formatted for Excel"""
    guards = Guard.objects.select_related("user").all()

    data = []
    for guard in guards:
        data.append(
            {
                "ID": guard.id,
                "Username": guard.user.username,
                "First Name": guard.user.first_name,
                "Last Name": guard.user.last_name,
                "Email": guard.user.email,
                "Phone": guard.phone,
                "Address": guard.address,
                "SSN": guard.ssn,
                "Is Armed": guard.is_armed,
                "Is Active": guard.user.is_active,
                "Date Joined": guard.user.date_joined.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

    return data


def _get_property_data() -> list[dict[str, Any]]:
    """Get Property data formatted for Excel"""
    properties = Property.objects.select_related("owner__user").all()

    data = []
    for prop in properties:
        owner_name = (
            f"{prop.owner.user.first_name} {prop.owner.user.last_name}".strip()
            if prop.owner
            else ""
        )

        data.append(
            {
                "ID": prop.id,
                "Name": prop.name or "",
                "Alias": prop.alias or "",
                "Address": prop.address,
                "Description": prop.description or "",
                "Owner": owner_name,
                "Owner Email": prop.owner.user.email if prop.owner else "",
                "Owner Phone": prop.owner.phone if prop.owner else "",
                "Created": prop.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "Updated": prop.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

    return data


def _get_shift_data() -> list[dict[str, Any]]:
    """Get Shift data formatted for Excel"""
    shifts = Shift.objects.select_related("guard__user", "property", "service").all()

    data = []
    for shift in shifts:
        guard_name = (
            f"{shift.guard.user.first_name} {shift.guard.user.last_name}".strip()
        )

        data.append(
            {
                "ID": shift.id,
                "Guard Name": guard_name,
                "Guard Username": shift.guard.user.username,
                "Property": shift.property.name or shift.property.address,
                "Property Address": shift.property.address,
                "Service": shift.service.name if shift.service else "",
                "Planned Start Time": shift.planned_start_time.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                if shift.planned_start_time
                else "",
                "Planned End Time": shift.planned_end_time.strftime("%Y-%m-%d %H:%M:%S")
                if shift.planned_end_time
                else "",
                "Start Time": shift.start_time.strftime("%Y-%m-%d %H:%M:%S")
                if shift.start_time
                else "",
                "End Time": shift.end_time.strftime("%Y-%m-%d %H:%M:%S")
                if shift.end_time
                else "",
                "Hours Worked": shift.hours_worked,
                "Planned Hours": float(shift.planned_hours_worked),
                "Status": shift.get_status_display(),
                "Is Armed": shift.is_armed,
                "Created": shift.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

    return data


def _get_client_data() -> list[dict[str, Any]]:
    """Get Client data formatted for Excel"""
    clients = Client.objects.select_related("user").all()

    data = []
    for client in clients:
        # Count properties for this client
        property_count = client.properties.count()

        # Get client name from user
        client_name = f"{client.user.first_name} {client.user.last_name}".strip()

        data.append(
            {
                "ID": client.id,
                "Name": client_name,
                "Username": client.user.username,
                "Email": client.user.email,
                "Phone": client.phone,
                "Balance": float(client.balance),
                "Properties Count": property_count,
                "Is Active": client.is_active,
                "Created": client.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "Updated": client.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

    return data


def _get_user_data() -> list[dict[str, Any]]:
    """Get User data formatted for Excel"""
    users = User.objects.all()

    data = []
    for user in users:
        # Check if user has a guard profile
        has_guard = hasattr(user, "guard")

        data.append(
            {
                "ID": user.pk,  # Use pk instead of id for MyPy compatibility
                "Username": user.username,
                "First Name": user.first_name,
                "Last Name": user.last_name,
                "Email": user.email,
                "Is Staff": user.is_staff,
                "Is Superuser": user.is_superuser,
                "Is Active": user.is_active,
                "Has Guard Profile": has_guard,
                "Date Joined": user.date_joined.strftime("%Y-%m-%d %H:%M:%S"),
                "Last Login": user.last_login.strftime("%Y-%m-%d %H:%M:%S")
                if user.last_login
                else "",
            }
        )

    return data


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def available_models(request):
    """
    Get list of available models for reporting
    """
    models = {
        "guard": {
            "name": "Guards",
            "description": "Security guard profiles with user information",
            "fields": [
                "ID",
                "Username",
                "First Name",
                "Last Name",
                "Email",
                "Phone",
                "Address",
                "SSN",
                "Is Armed",
                "Is Active",
                "Date Joined",
            ],
        },
        "property": {
            "name": "Properties",
            "description": "Property listings with owner information",
            "fields": [
                "ID",
                "Name",
                "Alias",
                "Address",
                "Description",
                "Owner",
                "Owner Email",
                "Owner Phone",
                "Created",
                "Updated",
            ],
        },
        "shift": {
            "name": "Shifts",
            "description": "Guard shift schedules and assignments",
            "fields": [
                "ID",
                "Guard Name",
                "Guard Username",
                "Property",
                "Property Address",
                "Service",
                "Planned Start Time",
                "Planned End Time",
                "Start Time",
                "End Time",
                "Hours Worked",
                "Planned Hours",
                "Status",
                "Is Armed",
                "Created",
            ],
        },
        "client": {
            "name": "Clients",
            "description": "Property owners and clients",
            "fields": [
                "ID",
                "Name",
                "Username",
                "Email",
                "Phone",
                "Balance",
                "Properties Count",
                "Is Active",
                "Created",
                "Updated",
            ],
        },
        "user": {
            "name": "Users",
            "description": "System users and accounts",
            "fields": [
                "ID",
                "Username",
                "First Name",
                "Last Name",
                "Email",
                "Is Staff",
                "Is Superuser",
                "Is Active",
                "Has Guard Profile",
                "Date Joined",
                "Last Login",
            ],
        },
    }

    return Response({"available_models": models, "total_count": len(models)})
