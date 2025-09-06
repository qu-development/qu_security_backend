from rest_framework.permissions import BasePermission

from .models import ApiKey


class HasAPIKey(BasePermission):
    """
    Allows access only to requests that have a valid and active API key.
    """

    def has_permission(self, request, view):
        """
        Check if request.auth is an instance of ApiKey.
        This permission relies on the ApiKeyAuthentication class having run first.
        """
        return isinstance(request.auth, ApiKey)
