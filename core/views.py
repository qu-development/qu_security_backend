"""
Core views for the application
"""

from django.http import HttpResponse, JsonResponse
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


@permission_classes([AllowAny])
def jwt_demo(request):
    """Serve the JWT demo HTML page"""
    # Read the HTML file
    import os

    from django.conf import settings

    html_path = os.path.join(settings.BASE_DIR, "JWT_DEMO.html")

    try:
        with open(html_path, encoding="utf-8") as f:
            html_content = f.read()
        return HttpResponse(html_content, content_type="text/html")
    except FileNotFoundError:
        return HttpResponse("Demo file not found", status=404)
