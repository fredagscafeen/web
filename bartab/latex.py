from pathlib import Path
import subprocess

from django.conf import settings
from django.template.loader import render_to_string

from .models import BarTabUser, BarTabSnapshot


class LatexError(Exception):
	def __init__(self, message):
		self.message = message


def generate_bartab(work_dir):
	file_prefix = 'bartab'

	with (Path(work_dir) / f'{file_prefix}.tex').open('w') as f:
		tab_parts = (([], 'Aktive'), ([], 'Inaktive'))
		for user in BarTabUser.objects.exclude(hidden_from_tab=True):
			tab_parts[not user.is_active][0].append(user)

		latex = render_to_string('bartab/bartab.tex', {
			'tab_parts': tab_parts,
			'pizza_lines': range(33),
			'latest_shift': BarTabSnapshot.objects.first().date,
			'logo_path': settings.STATIC_ROOT + f'images/logo_gray.png',
		})
		f.write(latex)

	p = subprocess.run(['latexmk', '-halt-on-error', '-pdf', f'{file_prefix}.tex'], cwd=work_dir, stdout=subprocess.PIPE)
	if p.returncode != 0:
		raise LatexError(str(p.stdout, 'utf-8'))

	return work_dir + f'/{file_prefix}.pdf'
