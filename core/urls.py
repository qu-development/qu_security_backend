from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from . import views
from .api import (
    ClientViewSet,
    CustomTokenObtainPairView,
    ExpenseViewSet,
    GuardPropertyTariffViewSet,
    GuardViewSet,
    PropertyTypeOfServiceViewSet,
    PropertyViewSet,
    ShiftViewSet,
    UserViewSet,
)

app_name = "core"

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")
router.register(r"guards", GuardViewSet, basename="guard")
router.register(r"clients", ClientViewSet, basename="client")
router.register(r"properties", PropertyViewSet, basename="property")
router.register(r"shifts", ShiftViewSet, basename="shift")
router.register(r"expenses", ExpenseViewSet, basename="expense")
router.register(
    r"property-types-of-service",
    PropertyTypeOfServiceViewSet,
    basename="property-type-of-service",
)
router.register(
    r"guard-property-tariffs",
    GuardPropertyTariffViewSet,
    basename="guard-property-tariff",
)

# The API URLs are now determined automatically by the router
urlpatterns = [
    # Authentication endpoints
    path("auth/login/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # Health check endpoint
    path("health/", views.health_check, name="health-check"),
    # JWT Demo endpoint
    path("demo/", views.jwt_demo, name="jwt-demo"),
    # API endpoints
    path("", include(router.urls)),
]
