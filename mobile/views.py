from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .authentication import ApiKeyAuthentication
from .permissions import HasAPIKey


class MobileDataView(APIView):
    """
    A sample view protected by API Key authentication.
    Only requests with a valid 'X-Api-Key' header will be granted access.
    """

    authentication_classes = [ApiKeyAuthentication]
    permission_classes = [HasAPIKey]

    def get(self, request, format=None):
        """
        Return a success message if the API key is valid.
        """
        content = {
            "status": _("success"),
            "message": _("API key authentication successful."),
        }
        return Response(content, status=status.HTTP_200_OK)
