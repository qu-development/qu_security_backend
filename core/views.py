"""
Core views for the application
"""

from django.http import JsonResponse
from django.utils.translation import gettext as _
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint to verify the API is running.
    """
    return JsonResponse(
        {
            "status": "ok",
            "message": _("API is running"),
            "language": request.LANGUAGE_CODE,
        }
    )
