import datetime

from django.db import models
from django.db.models import F, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from bartenders.models import BartenderShift

from .forms import SumValue, SumField as SumFormField


class SumField(models.TextField):
	def from_db_value(self, value, expression, connection):
		if value == '' or value == None:
			return None
		return SumFormField._parse_sum(value)

	def to_python(self, value):
		if isinstance(value, SumValue) or value == None:
			return value
		return SumFormField._parse_sum(value)

	def get_prep_value(self, value):
		if value == '' or value == None:
			return None

		if isinstance(value, str):
			return value

		return value.string

	def value_to_string(self, obj):
		""" Allows serialization of SumFields (dumpdata/loaddata) """
		value = self.value_from_object(obj)
		return self.get_prep_value(value)

	def formfield(self, **kwargs):
		return super().formfield(**{'form_class': SumFormField, **kwargs})


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

	def __str__(self):
		return f'{self.date}: {self.entries.count()} entries'


class BarTabEntry(models.Model):
	added = models.DecimalField(max_digits=9 + 2, decimal_places=2)
	used = models.DecimalField(max_digits=9 + 2, decimal_places=2)
	raw_added = SumField(blank=True)
	raw_used = SumField(blank=True)
	user = models.ForeignKey(BarTabUser, on_delete=models.CASCADE, related_name='entries')
	snapshot = models.ForeignKey(BarTabSnapshot, on_delete=models.CASCADE, related_name='entries')

	class Meta:
		unique_together = ('user', 'snapshot')
		ordering = (BarTabSnapshot.get_ordering('snapshot'),)

	def __str__(self):
		return f'{self.user} - {self.snapshot.date}'

	def clean(self):
		if self.raw_added:
			self.added = self.raw_added.value

		if self.raw_used:
			self.used = self.raw_used.value
