from django.utils.translation import gettext_lazy as _
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .models import ApiKey


class ApiKeyAuthentication(BaseAuthentication):
    """Custom authentication class for API Key based authentication."""

    def authenticate(self, request):
        """
        Authenticate the request by validating the API key from the 'X-Api-Key' header.
        """
        api_key = request.headers.get("X-Api-Key")
        if not api_key:
            # No API key provided, authentication cannot proceed.
            return None

        try:
            # Find an active API key that matches the one provided.
            api_key_obj = ApiKey.objects.get(key=api_key, is_active=True)
        except ApiKey.DoesNotExist:
            # Raise an exception if the key is not found or not active.
            raise AuthenticationFailed(_("Invalid or inactive API key."))

        # On success, return the ApiKey object as the 'auth' credential.
        # We return None for the user as this is system-to-system auth.
        return (None, api_key_obj)

    def authenticate_header(self, request):
        """
        Return a string to be used as the value of the `WWW-Authenticate`
        header in a 401 Unauthorized response.
        """
        return "Api-Key"
