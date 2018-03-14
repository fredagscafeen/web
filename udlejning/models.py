from bartenders.models import Bartender, BoardMember
from django.db import models


class Udlejning(models.Model):
	ASSOCIATION_CHOICES = (
		('internal', 'Intern'),
		('external', 'Ekstern'),
	)
	SYSTEM_CHOICES = (
		('small', 'Lille'),
		('medium', 'Mellem'),
	)

	dateFrom = models.DateTimeField()
	dateTo = models.DateTimeField(blank=True, null=True)
	whoReserved = models.CharField(max_length=140)
	association = models.CharField(max_length=16, choices=ASSOCIATION_CHOICES, blank=True)
	draftBeerSystem = models.CharField(max_length=16, choices=SYSTEM_CHOICES, blank=True)
	whoPays = models.CharField(max_length=140)
	paymentType = models.CharField(max_length=140)
	billSendTo = models.CharField(max_length=140)
	where = models.TextField(max_length=140)
	expectedConsummation = models.TextField(max_length=140)
	actualConsummation = models.TextField(max_length=140, blank=True)
	contactInfo = models.CharField(max_length=140)
	comments = models.TextField(blank=True)
	bartendersInCharge = models.ManyToManyField(Bartender, blank=True)
	paid = models.BooleanField(default=False)

	class Meta:
		ordering = ('dateFrom',)


class UdlejningGrill(models.Model):
	dateFrom = models.DateTimeField()
	dateTo = models.DateTimeField(blank=True, null=True)
	whoReserved = models.TextField(max_length=140)
	where = models.TextField(max_length=140)
	contactInfo = models.CharField(max_length=140)
	comments = models.TextField(blank=True)
	bartendersInCharge = models.ManyToManyField(Bartender, blank=True)

	class Meta:
		ordering = ('dateFrom',)
