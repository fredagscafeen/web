from django.db import models
from django.db.models import F, Sum, Value
from django.db.models.functions import Coalesce

from .forms import SumValue, SumField as SumFormField


class SumField(models.TextField):
	def from_db_value(self, value, expression, connection):
		if value == None:
			return value
		return SumFormField._parse_sum(value)


	def to_python(self, value):
		if isinstance(value, SumValue) or value == None:
			return value
		return SumFormField._parse_sum(value)


	def get_prep_value(self, value):
		if isinstance(value, str) or value == None:
			return value
		return value.string


	def formfield(self, **kwargs):
		return super().formfield(**{'form_class': SumFormField, **kwargs})



class BarTabUser(models.Model):
	name = models.CharField(max_length=140)
	email = models.EmailField(blank=True, null=True)
	hidden_from_tab = models.BooleanField(default=False)

	class Meta:
		ordering = ('name',)

	@property
	def balance(self):
		return self.entries.aggregate(balance=Coalesce(Sum(F('added') - F('used')), Value(0)))['balance']

	def __str__(self):
		return self.name


class BarTabSnapshot(models.Model):
	timestamp = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f'{self.timestamp.date()}: {self.entries.count()} entries'


class BarTabEntry(models.Model):
	added = models.DecimalField(max_digits=9 + 2, decimal_places=2)
	used = models.DecimalField(max_digits=9 + 2, decimal_places=2)
	raw_added = SumField(blank=True)
	raw_used = SumField(blank=True)
	user = models.ForeignKey(BarTabUser, on_delete=models.CASCADE, related_name='entries')
	snapshot = models.ForeignKey(BarTabSnapshot, on_delete=models.CASCADE, related_name='entries')

	class Meta:
		unique_together = ('user', 'snapshot')

	def __str__(self):
		return f'{self.user} - {self.snapshot.timestamp.date()}'

	def clean(self):
		print(repr(self.raw_added), repr(self.raw_used))
		if self.raw_added:
			self.added = self.raw_added.value

		if self.raw_used:
			self.used = self.raw_used.value

