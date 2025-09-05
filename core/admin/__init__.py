from django.contrib import admin

from core.models import (
    Client,
    Expense,
    Guard,
    Property,
    PropertyTypeOfService,
    Service,
    Shift,
    Weapon,
)

from .property import PropertyAdmin
from .service import ServiceAdmin

admin.site.register(Guard)
admin.site.register(Client)
admin.site.register(Property, PropertyAdmin)
admin.site.register(Shift)
admin.site.register(Expense)
admin.site.register(PropertyTypeOfService)
admin.site.register(Service, ServiceAdmin)
admin.site.register(Weapon)
