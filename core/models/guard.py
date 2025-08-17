from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import BaseModel


class Guard(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="guard")
    phone = models.CharField(max_length=20, blank=True, verbose_name=_("Phone"))
    ssn = models.CharField(max_length=20, blank=True, verbose_name=_("SSN"))
    address = models.CharField(max_length=255, blank=True, verbose_name=_("Address"))
    birth_date = models.DateField(null=True, blank=True, verbose_name=_("Birth date"))

    class Meta:
        verbose_name = _("Guard")
        verbose_name_plural = _("Guards")

    def __str__(self):
        return f"{self.user.username} - {_('Guard')}"
