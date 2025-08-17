from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, viewsets

from common.mixins import SoftDeleteMixin

from ..models import PropertyTypeOfService
from ..serializers import PropertyTypeOfServiceSerializer


class PropertyTypeOfServiceViewSet(SoftDeleteMixin, viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for PropertyTypeOfService model.

    list: Returns a list of all property types of service
    retrieve: Returns details for a property type of service by ID
    """

    queryset = PropertyTypeOfService.objects.all().order_by("name")
    serializer_class = PropertyTypeOfServiceSerializer

    def get_permissions(self):
        """Require authentication for all actions"""
        permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    @swagger_auto_schema(
        operation_description="Get list of all property types of service",
        responses={200: PropertyTypeOfServiceSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
