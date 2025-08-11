"""
URLs for permissions app
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .api import AdminPermissionAPI

# Create router for permission management API
router = DefaultRouter()

# Register Admin Permission API for centralized permission management
router.register(r"admin", AdminPermissionAPI, basename="admin-permissions")

urlpatterns = [
    path("api/v1/permissions/", include(router.urls)),
]
