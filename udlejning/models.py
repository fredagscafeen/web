from bartenders.models import Bartender
from django.db import models


class UdlejningCommon(models.Model):
	class Meta:
		abstract = True

	SYSTEM_CHOICES = (
		('small', 'Lille'),
		('medium', 'Mellem'),
	)

	PAYMENT_CHOICES = (
		('EAN', 'EAN'),
		('invoice', 'Faktura'),
		('card', 'Kort i baren'),
	)

	dateFrom = models.DateTimeField(verbose_name='Start dato & tid', help_text='Hvornår skal anlægget afhentes/stilles op?')
	dateTo = models.DateTimeField(blank=True, null=True, verbose_name='Slut dato & tid', help_text='Hvornår skal anlægget afleveres/pilles ned?')
	whoReserved = models.CharField(max_length=140, verbose_name='Hvem er I?')

	contactEmail = models.EmailField(verbose_name='Email til kontaktperson')
	contactPhone = models.IntegerField(verbose_name='Telefonnummer til kontaktperson', blank=True, null=True)

	draftBeerSystem = models.CharField(max_length=16, choices=SYSTEM_CHOICES, blank=True, verbose_name='Fadølsanlæg', help_text='Hvilket anlæg vil I låne?')
	whoPays = models.CharField(max_length=140, verbose_name='Hvem betaler?', help_text='Hvem skal regningen sendes til? (Fulde navn på person, virksomhed eller organisation)')
	paymentType = models.CharField(max_length=140, choices=PAYMENT_CHOICES, verbose_name='Betalingsform', help_text='Hvordan bliver der betalt?')

	EANnumber = models.IntegerField(verbose_name='EAN-nummer', blank=True, null=True, help_text='Skal kun angives, hvis der skal faktureres til et EAN-nummer')

	where = models.TextField(max_length=140, verbose_name='Lokation', help_text='Hvor bliver arrangmentet afholdt?')
	expectedConsummation = models.TextField(max_length=140, verbose_name='Forventet forbrug', help_text='Hvilke slags øl eller andre drikkevarer ønskes der og hvor mange fustager af hver type?')
	comments = models.TextField(blank=True, verbose_name='Kommentarer')


class Udlejning(UdlejningCommon):
	ASSOCIATION_CHOICES = (
		('internal', 'Intern'),
		('external', 'Ekstern'),
	)

	association = models.CharField(max_length=16, choices=ASSOCIATION_CHOICES, blank=True, verbose_name='Tilknytning')
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
