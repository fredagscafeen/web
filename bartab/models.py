import datetime
import re
from subprocess import run, CalledProcessError
from shlex import quote
from tempfile import TemporaryDirectory
import shutil
import os

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
	CREDIT_HOLD_LIMIT = 0

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
	notes = models.TextField(blank=True)

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
	HTLM5_MEDIA_DIR = '/var/lib/dokku/data/storage/fredagscafeen-media'

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
	def _htlm5_run(cls, *args, **kwargs):
		if not settings.DEBUG:
			args = ['ssh',
				    '-o', 'StrictHostKeyChecking=no',
				    '-i', 'media/ssh/id_rsa',
				    'remoteprint_relay@fredagscafeen.dk',
				    '--',
				    *args]


		print(*args)

		p = run(args, encoding='utf-8', check=True, capture_output=True, **kwargs)
		return p.stdout.strip()


	@classmethod
	def _cups_run(cls, *args, **kwargs):
		args = [args[0], '-h', cls.HOSTNAME, *args[1:]]

		return cls._htlm5_run(*args, **kwargs)

	@classmethod
	def is_connected(cls):
		out = cls._cups_run('lpstat', '-E', '-r')
		return out == 'scheduler is running'

	@classmethod
	def get_printers(cls):
		out = cls._cups_run('lpstat', '-E', '-p')

		for l in out.splitlines():
			if l.startswith('printer '):
				yield l.split()[1]

	def print(self, fname, inside_dokku=True):
		options = {
			'PageSize': 'A4',
			'Duplex': 'DuplexNoTumble',
			'StapleLocation': '4Staples',

			#'media': 'a4',
			#'orientation-requested': '4', # Landscape mode
			#'sides': 'two-sided-short-edge',
		}
		opt_args = sum((['-o', f'{quote(k)}={quote(v)}'] for k, v in options.items()), [])


		with TemporaryDirectory(dir=settings.MEDIA_ROOT) as d:
			os.chmod(d, 0o777)
			if settings.DEBUG or not inside_dokku:
				htlm5_name = fname
			else:
				tmp_dir = d.split('/')[-1]

				shutil.copy(fname, f'{d}/print.pdf')
				os.chmod(f'{d}/print.pdf', 0o777)

				htlm5_name = f'{self.HTLM5_MEDIA_DIR}/{tmp_dir}/print.pdf'

			out = self._cups_run('lp',
						  '-E',
						  '-d', self.name,
						  *opt_args,
						  '--',
						  htlm5_name)


		prefix = 'request id is '
		suffix = ' (1 file(s))'
		assert out.startswith(prefix)
		assert out.endswith(suffix)
		return out[len(prefix):-len(suffix)]

	@classmethod
	def get_status(cls, job_id):
		out = cls._cups_run('lpstat',
		                    '-E',
							'-l')

		status = {}
		lines = out.splitlines()
		for i in range(len(lines)):
			if lines[i].startswith(job_id):
				i += 1
				while i < len(lines) and lines[i].startswith('\t'):
					parts = lines[i].strip().split(': ', maxsplit=1)
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
