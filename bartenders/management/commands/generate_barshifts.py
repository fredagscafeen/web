import datetime
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from bartenders.models import Bartender, BartenderShift, BartenderShiftPeriod, next_bartender_shift_start
import random
from itertools import count
import copy
from collections import defaultdict
import sys


# TODO: Create web interface for entering these:
EXCLUSIONS = '''
*** REDACTED ***
'''

class Command(BaseCommand):
	help = 'Generate normal barshifts'

	BARTENDER_SHIFTS = 2
	BARTENDERS_PER_SHIFT = 4

	def add_arguments(self, parser):
		parser.add_argument('-t', '--max-tries', type=int, default=10**4)

	def try_random_solution(self, total_shifts, sorted_bartenders, bartenders_needed, available_shifts):
		available_shifts = copy.deepcopy(available_shifts)

		total_needed = total_shifts * bartenders_needed
		shifts_for_bartender = [0] * len(sorted_bartenders)

		shifts = [[] for _ in range(total_shifts)]
		for i in range(self.BARTENDER_SHIFTS):
			if i == self.BARTENDER_SHIFTS - 1:
				sorted_bartenders = random.sample(sorted_bartenders, total_needed)

			for b in sorted_bartenders:
				while True:
					if len(available_shifts[b]) == 0:
						break

					s = random.choice(list(available_shifts[b]))

					available_shifts[b].remove(s)
					if len(shifts[s]) != bartenders_needed:
						shifts_for_bartender[b] += 1
						total_needed -= 1
						shifts[s].append(b)
						break

		# Failed to get solution
		if total_needed != 0:
			# print('  Couldn\'t solve it!')
			return None

		# Solution is too skewed
		if min(shifts_for_bartender) + 1 < max(shifts_for_bartender):
			# print('  Solution is too skewed!')
			return None

		return shifts

	def get_shifts_score(self, bartenders, shifts):
		min_distance = float('inf')
		last_shift = [None for _ in bartenders]
		for s, bs in enumerate(shifts):
			for b in bs:
				if last_shift[b] != None:
					min_distance = min(min_distance, s - last_shift[b])

				last_shift[b] = s

		return min_distance

	def get_random_solution(self, total_shifts, bartenders, bartenders_needed, available_shifts, max_tries):
		best = (-float('inf'), None)

		sorted_bartenders = sorted(range(len(bartenders)), key=lambda x: len(available_shifts[x]))
		i = 0
		while i < max_tries:
			result = self.try_random_solution(total_shifts,
					sorted_bartenders, bartenders_needed, available_shifts)

			if result != None:
				print(f'\r{i + 1} / {max_tries}', end='')
				sys.stdout.flush()
				i += 1
				best = max(best, (self.get_shifts_score(bartenders, result), result))

		print()
		print(f'Min distance: {best[0]}')
		return best[1]


	def handle(self, *args, **options):
		board_members = list(Bartender.objects.filter(boardmember__isnull=False))
		normal_bartenders = list(Bartender.objects.filter(isActiveBartender=True, boardmember__isnull=True))

		all_bartenders = [normal_bartenders, board_members]

		total_shifts = min(self.BARTENDER_SHIFTS * len(board_members),
				           self.BARTENDER_SHIFTS * len(normal_bartenders) // (self.BARTENDERS_PER_SHIFT - 1))

		last_shift = BartenderShift.objects.last()

		shift_starts = [next_bartender_shift_start(last_shift.start_datetime.date())]
		for _ in range(total_shifts - 1):
			shift_starts.append(next_bartender_shift_start(shift_starts[-1].date()))

		shift_indices = {dt.date(): i for i, dt in enumerate(shift_starts)}

		print(f'Board members: {len(board_members)}')
		print(f'Other active bartenders: {len(normal_bartenders)}')
		print(f'Generating {total_shifts} shifts from {shift_starts[0].date()} to {shift_starts[-1].date()}')

		available_shifts = [[set(range(total_shifts)) for _ in all_bartenders[i]]
		                     for i in range(2)]

		current_bartender = None
		for l in EXCLUSIONS.splitlines():
			if l == '':
				current_bartender = None
			else:
				if current_bartender == None:
					current_bartender = Bartender.objects.get(email=l)
				else:
					year = datetime.datetime.now().year
					date = datetime.datetime.strptime(f'{year} {l}', '%Y %d/%m').date()
					shift = shift_indices.get(date)
					if shift == None:
						if shift_starts[0].date() <= date <= shift_starts[-1].date():
							print(f'WARNING: {date} is between first and last shift, but is not a friday')
						continue

					index = all_bartenders[current_bartender.isBoardMember].index(current_bartender)
					assert index != -1
					available_shifts[current_bartender.isBoardMember][index].remove(shift)

		shifts = []
		for board_member, bartenders in enumerate(all_bartenders):
			bartenders_needed = 1 if board_member else self.BARTENDERS_PER_SHIFT - 1
			shifts.append(self.get_random_solution(total_shifts,
				bartenders, bartenders_needed, available_shifts[board_member],
				options['max_tries']))

		shifts_for_bartender = defaultdict(int)
		for s, dt in enumerate(shift_starts):
			print(f'{dt}:')
			for board_member, bartenders in reversed(list(enumerate(all_bartenders))):
				for b in shifts[board_member][s]:
					shifts_for_bartender[(board_member, b)] += 1
					print(f'  {bartenders[b]}')

			print()

		print(f'Bartenders with fewer than {self.BARTENDER_SHIFTS} shifts:')
		for (board_member, b), shift_count in shifts_for_bartender.items():
			if shift_count < self.BARTENDER_SHIFTS:
				print(f'  {all_bartenders[board_member][b]}: {shift_count} shifts')

		print()

		while True:
			r = input('Publish? [yN] ').lower()
			if r in ['', 'n']:
				return

			if r == 'y':
				break

		print()
		print('Publishing...')

		period = BartenderShiftPeriod.objects.create()

		for s, dt in enumerate(shift_starts):
			responsible = all_bartenders[True][shifts[True][s][0]]
			other_bartenders = [all_bartenders[False][b] for b in shifts[False][s]]

			shift = BartenderShift.objects.create(start_datetime=dt,
												  responsible=responsible,
			                                      period=period)

			shift.other_bartenders.set(other_bartenders)
			shift.save()
