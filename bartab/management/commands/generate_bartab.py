from django.core.management.base import BaseCommand

from bartab.latex import generate_bartab

class Command(BaseCommand):
	help = 'Generates the bartab pdf'

	def add_arguments(self, parser):
		parser.add_argument('output_dir')

	def handle(self, *args, **options):
		d = options['output_dir']
		res_file = generate_bartab(d)
		print(f'PDF was generated at: {res_file}')
