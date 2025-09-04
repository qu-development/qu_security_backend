# Re-export viewsets and auth views from submodules for backward compatibility
from .auth import CustomTokenObtainPairSerializer, CustomTokenObtainPairView
from .clients import ClientViewSet
from .expenses import ExpenseViewSet
from .guards import GuardViewSet
from .properties import PropertyViewSet
from .property_types import PropertyTypeOfServiceViewSet
from .shifts import ShiftViewSet
from .tariffs import GuardPropertyTariffViewSet
from .users import UserViewSet
from .weapons import WeaponViewSet

__all__ = [
    "CustomTokenObtainPairSerializer",
    "CustomTokenObtainPairView",
    "UserViewSet",
    "GuardViewSet",
    "ClientViewSet",
    "PropertyViewSet",
    "ShiftViewSet",
    "ExpenseViewSet",
    "PropertyTypeOfServiceViewSet",
    "GuardPropertyTariffViewSet",
    "WeaponViewSet",
]
