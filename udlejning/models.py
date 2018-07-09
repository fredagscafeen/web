from bartenders.models import Bartender
from django.db import models


class UdlejningCommon(models.Model):
	class Meta:
		abstract = True

	ASSOCIATION_CHOICES = (
		('internal', 'Intern'),
		('external', 'Ekstern'),
	)
	SYSTEM_CHOICES = (
		('small', 'Lille'),
		('medium', 'Mellem'),
	)

	dateFrom = models.DateTimeField(verbose_name='Start dato')
	dateTo = models.DateTimeField(blank=True, null=True, verbose_name='Slut dato')
	whoReserved = models.CharField(max_length=140, verbose_name='Hvem er I?')
	association = models.CharField(max_length=16, choices=ASSOCIATION_CHOICES, blank=True, verbose_name='Tilknytning')
	draftBeerSystem = models.CharField(max_length=16, choices=SYSTEM_CHOICES, blank=True, verbose_name='Fadølsanlæg')
	whoPays = models.CharField(max_length=140, verbose_name='Hvem betaler?')
	paymentType = models.CharField(max_length=140, verbose_name='Hvordan vil I betale?')
	where = models.TextField(max_length=140, verbose_name='Hvor skal det bruges?')
	expectedConsummation = models.TextField(max_length=140, verbose_name='Forventet forbrug')
	contactInfo = models.CharField(max_length=140, verbose_name='Kontaktinformation')
	comments = models.TextField(blank=True, verbose_name='Kommentarer')


class Udlejning(UdlejningCommon):
	actualConsummation = models.TextField(max_length=140, blank=True)
	bartendersInCharge = models.ManyToManyField(Bartender, blank=True)
	billSendTo = models.CharField(max_length=140)
	paid = models.BooleanField(default=False)

	class Meta:
		ordering = ('dateFrom',)


class UdlejningApplication(UdlejningCommon):
	created = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ('created',)

	def accept(self):
		common_fields = super()._meta.get_fields()
		value_dict = {f.name: getattr(self, f.name) for f in common_fields}
		u = Udlejning.objects.create(**value_dict)
		return u.pk


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
