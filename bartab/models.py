import datetime
import re
from subprocess import check_output, CalledProcessError

from django.db import models
from django.db.models import F, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.conf import settings

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


class Printer(models.Model):
	HOSTNAME = 'localhost' if settings.DEBUG else 'localhost:6631'

	class PrinterChoiceIter:
		def __iter__(self):
			yield (None, '-' * 9)
			try:
				for p in Printer.get_printers():
					yield (p, p)
			except CalledProcessError:
				# Ignore this error as it will happen during dokku building
				pass

	name = models.CharField(max_length=32, unique=True)

	@classmethod
	def get_printers(cls):
		out = check_output(['lpstat', '-h', cls.HOSTNAME,
		                    '-E',
							'-p'], encoding='utf-8')

		for l in out.strip().splitlines():
			if l.startswith('printer '):
				yield l.split()[1]

	def print(self, fname):
		options = {
			'PageSize': 'a4',
			'Duplex': 'DuplexTumble',
			'StapleLocation': '4Staples',

			#'media': 'a4',
			#'orientation-requested': '4', # Landscape mode
			#'sides': 'two-sided-short-edge',
		}
		opt_args = sum((['-o', f'{k}={v}'] for k, v in options.items()), [])
		out = check_output(['lp', '-h', self.HOSTNAME,
		              '-E',
					  '-d', self.name,
					  *opt_args,
					  '--',
					  fname], encoding='utf-8').strip()

		prefix = 'request id is '
		suffix = ' (1 file(s))'
		assert out.startswith(prefix)
		assert out.endswith(suffix)
		return out[len(prefix):-len(suffix)]

	@classmethod
	def get_status(cls, job_id):
		out = check_output(['lpstat', '-h', cls.HOSTNAME,
		                    '-E',
							'-W', 'all',
							'-l'], encoding='utf-8')

		status = {}
		lines = out.splitlines()
		for i in range(len(lines)):
			if lines[i].startswith(job_id):
				i += 1
				while i < len(lines) and lines[i].startswith(' '):
					parts = lines[i].strip().split(': ')
					if len(parts) == 2:
						status[parts[0]] = parts[1]

					i += 1

				break
		else:
			# Not found, probably done
			return 'done', None

		if 'Status' in status:
			s = status['Status']

			m = re.search(r'NT_\S+', s)
			if m:
				status_code = m.group()
				return 'error', status_code

			return 'done', None
		else:
			return 'unknown', None

	def clean_name(self):
		name = self.cleaned_data['name']
		if name not in self.get_printers():
			raise ValidationError(f'Kunne ikke finde printeren "{name}"')

	def __str__(self):
		return self.name
