from django.db import models
from django.utils.translation import gettext_lazy as _

from bartenders.models import Bartender


class MailingList(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name=_("Navn"))
    members = models.ManyToManyField(
        Bartender, related_name="shifts", blank=True, verbose_name=_("Modtagere")
    )
