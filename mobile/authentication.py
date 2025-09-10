from django.utils.translation import gettext_lazy as _
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from core.models import Guard

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


class MobileGuardAuthentication(BaseAuthentication):
    """
    Custom authentication class for mobile app using X-API-KEY and X-Guard-ID headers.

    This authenticates guards from the mobile app using:
    - X-API-KEY: A server key for API access validation
    - X-Guard-ID: The guard's ID to identify the specific guard
    """

    def authenticate(self, request):
        """
        Authenticate the request using X-API-KEY and X-Guard-ID headers.
        """
        api_key = request.headers.get("X-API-KEY")
        guard_id = request.headers.get("X-Guard-ID")

        if not api_key or not guard_id:
            # Both headers are required for mobile authentication
            return None

        try:
            ApiKey.objects.get(key=api_key, is_active=True)
        except ApiKey.DoesNotExist:
            raise AuthenticationFailed(_("Invalid or inactive API key."))

        # Validate the guard exists and is active
        try:
            guard = Guard.objects.select_related("user").get(
                id=guard_id, user__is_active=True
            )
        except Guard.DoesNotExist:
            raise AuthenticationFailed(_("Invalid guard ID or guard is inactive."))

        # Return the guard's user and the guard object as authentication
        return (guard.user, guard)

    def authenticate_header(self, request):
        """
        Return a string to be used as the value of the `WWW-Authenticate`
        header in a 401 Unauthorized response.
        """
        return "Mobile-Guard-Auth"
