from bartenders.models import Bartender
from django.db import models


class Udlejning(models.Model):
    dateFrom = models.DateTimeField()
    dateTo = models.DateTimeField(blank=True, null=True)
    whoReserved = models.CharField(max_length=140)
    whoPays = models.CharField(max_length=140)
    paymentType = models.CharField(max_length=140)
    billSendTo = models.CharField(max_length=140)
    where = models.TextField(max_length=140)
    expectedConsummation = models.TextField(max_length=140)
    actualConsummation = models.TextField(max_length=140, blank=True, null=True)
    contactInfo = models.CharField(max_length=140)
    comments = models.TextField(blank=True, null=True)
    bartenderInCharge = models.ForeignKey(Bartender, blank=True, null=True)
    paid = models.BooleanField(default=False)

    class Meta:
        ordering = ('dateFrom', )


class UdlejningGrill(models.Model):
    dateFrom = models.DateTimeField()
    dateTo = models.DateTimeField(blank=True, null=True)
    whoReserved = models.TextField(max_length=140)
    where = models.TextField(max_length=140)
    contactInfo = models.CharField(max_length=140)
    comments = models.TextField(blank=True, null=True)
    bartenderInCharge = models.ForeignKey(Bartender, blank=True, null=True)

    class Meta:
        ordering = ('dateFrom', )
