from django.db import models
from django.utils.translation import gettext_lazy as _

from bartenders.models import Bartender


class MailingList(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name=_("Navn"))
    isOnlyInternal = models.BooleanField(
        default=False,
        verbose_name=_("Only list members can send to this mailing list"),
    )
    members = models.ManyToManyField(
        Bartender, related_name="mailing_lists", verbose_name=_("Medlemmer")
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Mailingliste")
        verbose_name_plural = _("Mailinglister")
        ordering = ["name"]

    def save(self, *args, **kwargs):
        self.name = self.name.lower()
        super().save(*args, **kwargs)

    @property
    def count(self):
        return self.members.count()
