from django.contrib import admin

from .models import Client, Expense, Guard, Property, Shift

admin.site.register(Guard)
admin.site.register(Client)
admin.site.register(Property)
admin.site.register(Shift)
admin.site.register(Expense)
