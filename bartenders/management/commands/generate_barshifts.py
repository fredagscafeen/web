import datetime
from django.core.management.base import BaseCommand
from bartenders.models import Bartender, BartenderShift, BartenderShiftPeriod, next_bartender_shift_start, BartenderUnavailableDate
import random
import copy
from collections import defaultdict
import sys


# This needs to be changed before generating shifts
'''
EXTRA_SHIFTS = [
	# Rusuge
	(datetime.datetime(2018, 8, 24, 21), datetime.datetime(2018, 8, 25, 2)),
]

EXTRA_SHIFTS = [tuple(map(timezone.get_default_timezone().localize, period)) for period in EXTRA_SHIFTS]
'''

EXTRA_SHIFTS = []

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

	def get_shifts_score(self, bartenders, shifts, last_shifts):
		count = 0
		min_distance = float('inf')
		for s, bs in enumerate(shifts):
			for b in bs:
				if last_shifts[b] != None:
					distance = s - last_shifts[b]
					if distance < min_distance:
						min_distance = distance
						count = 1
					elif distance == min_distance:
						count += 1

				last_shifts[b] = s

		return (min_distance, count)

	def get_random_solution(self, total_shifts, bartenders, bartenders_needed, available_shifts, max_tries, last_shifts):
		best = ((-float('inf'), 0), None)

		sorted_bartenders = sorted(range(len(bartenders)), key=lambda x: len(available_shifts[x]))
		i = 0
		while i < max_tries:
			result = self.try_random_solution(total_shifts,
					sorted_bartenders, bartenders_needed, available_shifts)

			if result != None:
				print(f'\r{i + 1} / {max_tries}', end='')
				sys.stdout.flush()
				i += 1
				best = max(best, (self.get_shifts_score(bartenders, result, last_shifts), result))

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
		for _ in range(total_shifts - 1 - len(EXTRA_SHIFTS)):
			shift_starts.append(next_bartender_shift_start(shift_starts[-1].date()))

		shift_periods = sorted([(start, None) for start in shift_starts] + [s for s in EXTRA_SHIFTS])

		shift_indices = defaultdict(list)
		for i, (start, end) in enumerate(shift_periods):
			shift_indices[start.date()].append(i)

		print(f'Board members: {len(board_members)}')
		print(f'Other active bartenders: {len(normal_bartenders)}')
		print(f'Generating {total_shifts} shifts from {shift_starts[0].date()} to {shift_starts[-1].date()}')

		last_shifts = []
		for bs in all_bartenders:
			l = []
			for b in bs:
				s = b.last_bartender_shift
				if s != None:
					s = (s.date - last_shift.date + datetime.timedelta(weeks=1)).days // 7 - 1
				l.append(s)
			last_shifts.append(l)

		available_shifts = [[set(range(total_shifts)) for _ in all_bartenders[i]]
		                     for i in range(2)]

		# Could be filtered
		unavailable_dates = BartenderUnavailableDate.objects.all()

		for d in unavailable_dates:
			bartender = d.bartender

			if not bartender.isActiveBartender:
				continue

			shifts = shift_indices.get(d.date)
			if shifts == None:
				if shift_periods[0][0].date() <= d.date <= shift_periods[-1][0].date():
					print(f'WARNING: {d.date} is between first and last shift, but is not a friday')

				continue

			index = all_bartenders[bartender.isBoardMember].index(bartender)
			for shift in shifts:
				available_shifts[bartender.isBoardMember][index].remove(shift)


		shifts = []
		for board_member, (bartenders, ls) in enumerate(zip(all_bartenders, last_shifts)):
			bartenders_needed = 1 if board_member else self.BARTENDERS_PER_SHIFT - 1
			shifts.append(self.get_random_solution(total_shifts,
				bartenders, bartenders_needed, available_shifts[board_member],
				options['max_tries'], ls))

		shifts_for_bartender = defaultdict(int)
		for s, (start, end) in enumerate(shift_periods):
			print(f'{start}:')
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

		for s, (start, end) in enumerate(shift_periods):
			responsible = all_bartenders[True][shifts[True][s][0]]
			other_bartenders = [all_bartenders[False][b] for b in shifts[False][s]]

			shift = BartenderShift.objects.create(start_datetime=start,
					                              end_datetime=end,
												  responsible=responsible,
			                                      period=period)

			shift.other_bartenders.set(other_bartenders)
			shift.save()
