import re
from subprocess import run, CalledProcessError
from shlex import quote
from tempfile import TemporaryDirectory
import shutil
import os

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


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
