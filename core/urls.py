from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .api import (
    UserViewSet, CustomTokenObtainPairView, GuardViewSet, 
    ClientViewSet, PropertyViewSet, ShiftViewSet, ExpenseViewSet
)

app_name = 'core'

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'guards', GuardViewSet, basename='guard')
router.register(r'clients', ClientViewSet, basename='client')
router.register(r'properties', PropertyViewSet, basename='property')
router.register(r'shifts', ShiftViewSet, basename='shift')
router.register(r'expenses', ExpenseViewSet, basename='expense')

# The API URLs are now determined automatically by the router
urlpatterns = [
    # Authentication endpoints
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # User CRUD endpoints
    path('', include(router.urls)),
]
