from rest_framework import generics

from .models import GeneralSettings
from .serializers import GeneralSettingsSerializer


class GeneralSettingsRetrieveView(generics.RetrieveAPIView):
    """
    Read-only endpoint for the GeneralSettings singleton.
    """

    serializer_class = GeneralSettingsSerializer

    def get_object(self):
        # Return the singleton instance from django-solo
        return GeneralSettings.get_solo()
