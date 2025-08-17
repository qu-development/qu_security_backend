# Re-export serializers from submodules for backward compatibility
from .clients import (
    ClientCreateSerializer,
    ClientDetailSerializer,
    ClientSerializer,
    ClientUpdateSerializer,
)
from .expenses import ExpenseSerializer
from .guards import GuardCreateSerializer, GuardDetailSerializer, GuardSerializer
from .properties import PropertyDetailSerializer, PropertySerializer
from .property_types import PropertyTypeOfServiceSerializer
from .shifts import ShiftSerializer
from .tariffs import GuardPropertyTariffSerializer
from .users import (
    LoginSerializer,
    UserCreateSerializer,
    UserSerializer,
    UserUpdateSerializer,
)

__all__ = [
    # users
    "UserSerializer",
    "UserCreateSerializer",
    "UserUpdateSerializer",
    "LoginSerializer",
    # guards
    "GuardCreateSerializer",
    "GuardSerializer",
    "GuardDetailSerializer",
    # clients
    "ClientSerializer",
    "ClientDetailSerializer",
    "ClientCreateSerializer",
    "ClientUpdateSerializer",
    # property types
    "PropertyTypeOfServiceSerializer",
    # properties
    "PropertySerializer",
    "PropertyDetailSerializer",
    # shifts
    "ShiftSerializer",
    # expenses
    "ExpenseSerializer",
    # tariffs
    "GuardPropertyTariffSerializer",
]
