import datetime

from django.db import models
from django.db.models import F, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.core.exceptions import ValidationError

from bartenders.models import BartenderShift

from .sumfield import SumField


class BarTabUser(models.Model):
	ACTIVE_TIME_LIMIT = datetime.timedelta(weeks=4)
	CREDIT_HOLD_LIMIT = -100

	name = models.CharField(max_length=140)
	email = models.EmailField(blank=True, null=True)
	hidden_from_tab = models.BooleanField(default=False)

	class Meta:
		ordering = ('name',)

	@property
	def balance(self):
		return self.entries.aggregate(balance=Coalesce(Sum(F('added') - F('used')), Value(0)))['balance']

	@property
	def balance_str(self):
		return str(self.balance).replace('.', ',')

	@property
	def has_credit_hold(self):
		return self.balance <= self.CREDIT_HOLD_LIMIT

	@property
	def is_active(self):
		latest_entry = self.entries.first()
		if not latest_entry:
			return False

		return timezone.now() - latest_entry.snapshot.datetime < self.ACTIVE_TIME_LIMIT

	def __str__(self):
		return self.name


def bar_tab_snapshot_ordering(related_name=None):
	field_path = 'bartender_shift__start_datetime'
	if related_name:
		field_path = f'{related_name}__{field_path}'

	return F(field_path).desc(nulls_last=True)


class BarTabSnapshot(models.Model):
	bartender_shift = models.OneToOneField(BartenderShift, on_delete=models.PROTECT, related_name='bar_tab_snapshot', blank=True, null=True)
	last_updated = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = (bar_tab_snapshot_ordering(),)

	@staticmethod
	def get_ordering(related_name=None):
		return bar_tab_snapshot_ordering(related_name)

	@property
	def datetime(self):
		if not self.bartender_shift:
			return timezone.make_aware(datetime.datetime.fromtimestamp(0))

		return self.bartender_shift.start_datetime

	@property
	def date(self):
		return self.datetime.date()

	@property
	def total_added(self):
		return self.entries.aggregate(total_added=Sum('added'))['total_added']

	@property
	def total_used(self):
		return self.entries.aggregate(total_used=Sum('used'))['total_used']

	def __str__(self):
		return f'{self.date}: {self.entries.count()} entries'


class BarTabEntry(models.Model):
	added_cash = models.NullBooleanField(blank=True, verbose_name='Kontant?')
	added = models.DecimalField(max_digits=9 + 2, decimal_places=2)
	used = models.DecimalField(max_digits=9 + 2, decimal_places=2)
	raw_added = SumField(blank=True, verbose_name='Indsat')
	raw_used = SumField(blank=True, verbose_name='Køb')
	user = models.ForeignKey(BarTabUser, on_delete=models.CASCADE, related_name='entries', verbose_name='Bruger')
	snapshot = models.ForeignKey(BarTabSnapshot, on_delete=models.CASCADE, related_name='entries')

	class Meta:
		unique_together = ('user', 'snapshot')
		ordering = (BarTabSnapshot.get_ordering('snapshot'),)

	def __str__(self):
		return f'{self.user} - {self.snapshot.date}'

	def clean(self):
		if self.raw_added:
			self.added = self.raw_added.value
			if self.added_cash == None and self.added != 0:
				raise ValidationError('Vælg kontant eller ej.')

		if self.raw_used:
			self.used = self.raw_used.value
