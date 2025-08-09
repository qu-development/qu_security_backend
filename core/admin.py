from django.contrib import admin
from .models import Guard, Client, Property, Shift, Expense

admin.site.register(Guard)
admin.site.register(Client)
admin.site.register(Property)
admin.site.register(Shift)
admin.site.register(Expense)
