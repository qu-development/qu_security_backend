from django.http import JsonResponse
from django.utils.translation import gettext as _
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

# Create your views here.


@api_view(["GET"])
@permission_classes([AllowAny])
def test_translations(request):
    """
    Test endpoint to verify translations are working correctly.
    """
    translations = {
        "guard": _("Guard"),
        "client": _("Client"),
        "property": _("Property"),
        "shift": _("Shift"),
        "expense": _("Expense"),
        "username": _("Username"),
        "email": _("Email address"),
        "first_name": _("First name"),
        "last_name": _("Last name"),
        "phone": _("Phone number"),
        "address": _("Address"),
        "name": _("Name"),
        "description": _("Description"),
        "location": _("Location"),
        "start_time": _("Start time"),
        "end_time": _("End time"),
        "date": _("Date"),
        "amount": _("Amount"),
        "user": _("User"),
    }

    return JsonResponse(
        {
            "message": _("Translations test endpoint"),
            "translations": translations,
            "language": request.LANGUAGE_CODE,
        }
    )
