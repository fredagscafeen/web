from bartenders.models import BoardMember
from django.db import models


class Udlejning(models.Model):
    dateFrom = models.DateTimeField()
    dateTo = models.DateTimeField(blank=True, null=True)
    whoReserved = models.TextField(max_length=140)
    whoPays = models.TextField(max_length=140)
    paymentType = models.CharField(max_length=140)
    paymentSendTo = models.CharField(max_length=140)
    where = models.TextField(max_length=140)
    expectedConsummation = models.TextField(max_length=140)
    actualConsummation = models.TextField(max_length=140, blank=True, null=True)
    contactInfo = models.CharField(max_length=140)
    comments = models.TextField(blank=True, null=True)
    boardMemberInCharge = models.ForeignKey(BoardMember, blank=True, null=True)
    paid = models.BooleanField(default=False)
