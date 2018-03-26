import datetime
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from bartenders.models import Bartender, BoardMember, BartenderShift
import z3


EXCLUSIONS = '''
*** REDACTED ***
'''

class Command(BaseCommand):
	help = 'Generate normal barshifts'

	def add_arguments(self, parser):
		parser.add_argument('--dry-run', action='store_true')

	def handle(self, *args, **options):
		BARTENDER_SHIFTS = 2
		BARTENDERS_PER_SHIFT = 4

		board_members = list(Bartender.objects.filter(boardmember__isnull=False))
		normal_bartenders = list(Bartender.objects.filter(isActiveBartender=True, boardmember__isnull=True))
		all_bartenders = board_members + normal_bartenders

		total_bartenders = len(all_bartenders)

		total_shifts = min(BARTENDER_SHIFTS * len(board_members), BARTENDER_SHIFTS * len(normal_bartenders) // (BARTENDERS_PER_SHIFT - 1))

		last_shift = BartenderShift.objects.last()

		# This might be problematic if DST is changing
		shift_starts = [last_shift.start_datetime + datetime.timedelta(7) * (i + 1)
		                for i in range(total_shifts)]

		shift_indices = {dt.date(): i for i, dt in enumerate(shift_starts)}

		print(f'Board members: {len(board_members)}')
		print(f'Other active bartenders: {len(normal_bartenders)}')
		print(f'Generating {total_shifts} shifts from {shift_starts[0].date()} to {shift_starts[-1].date()}')

		# variables[s][b]
		variables = [[z3.Int(f'x_{b},{s}') for b in range(total_bartenders)]
				      for s in range(total_shifts)]

		opt = z3.Optimize()

		# Ensure only 0 and 1 assignments
		for xs in variables:
			for x in xs:
				opt.add(0 <= x)
				opt.add(x <= 1)

		for s in range(total_shifts):
			# There should be exactly one boardmember on a shift
			opt.add(sum(variables[s][:len(board_members)]) == 1)

			# There should be exactly BARTENDERS_PER_SHIFT - 1 other bartenders
			opt.add(sum(variables[s][len(board_members):]) == BARTENDERS_PER_SHIFT - 1)

		for b in range(total_bartenders):
			opt.add(sum(variables[s][b] for s in range(total_shifts)) >= BARTENDER_SHIFTS)


		objective_function = 0

		current_bartender = None
		for l in EXCLUSIONS.splitlines():
			if l == '':
				current_bartender = None
			else:
				if current_bartender == None:
					current_bartender = all_bartenders.index(Bartender.objects.get(email=l))
					assert current_bartender != -1
				else:
					year = datetime.datetime.now().year
					date = datetime.datetime.strptime(f'{year} {l}', '%Y %d/%m').date()
					shift = shift_indices.get(date)
					if shift == None:
						if shift_starts[0].date() <= date <= shift_starts[-1].date():
							print(f'WARNING: {date} is between first and last shift, but is not a friday')
						continue

					objective_function += variables[shift][current_bartender]

		opt.add(objective_function == 0)
		obj = opt.minimize(objective_function)

		print(opt.sexpr())

		print('Solving...')
		if opt.check() != z3.sat:
			raise CommandError('Linear Program cannot be satisfied!')

		model = opt.model()


		lo = opt.lower(obj)
		up = opt.upper(obj)
		assert lo == up

		print(f'Got solution with {lo} conflicts')

		for s, dt in enumerate(shift_starts):
			print(f'{dt}:')
			for b, bartender in enumerate(all_bartenders):
				if model[variables[s][b]] == 1:
					print(f'  {b}: {bartender}')

			print()

		#print(model)
