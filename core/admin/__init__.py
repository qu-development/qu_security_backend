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
from core.models import (
    Note as Note,
)

from .guard import GuardAdmin
from .note import (
    NoteAdmin as NoteAdmin,
)
from .property import PropertyAdmin
from .service import ServiceAdmin
from .shift import ShiftAdmin

admin.site.register(Guard, GuardAdmin)
admin.site.register(Client)
admin.site.register(Property, PropertyAdmin)
admin.site.register(Shift, ShiftAdmin)
admin.site.register(Expense)
admin.site.register(PropertyTypeOfService)
admin.site.register(Service, ServiceAdmin)
admin.site.register(Weapon)
