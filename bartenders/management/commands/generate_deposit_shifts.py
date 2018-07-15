from django.core.management.base import BaseCommand, CommandError
from bartenders.models import Bartender, BoardMember, BoardMemberDepositShift, BoardMemberDepositShiftPeriod, next_deposit_shift_start
import random
from itertools import zip_longest, chain
import datetime


class Command(BaseCommand):
	help = 'Generates new deposit shifts'

	RESPONSIBLES = 2
	WEEKS = 4

	def handle(self, *args, **options):
		board_members = set(Bartender.objects.filter(boardmember__isnull=False))

		first_shift = None
		for shift in reversed(BoardMemberDepositShift.objects.all()):
			if shift.responsibles.count() == self.RESPONSIBLES:
				break

			first_shift = shift


		assert first_shift != None
		assert len(first_shift.responsibles.all()) == 1

		last_responsibles = BoardMemberDepositShift.objects.get(start_date=first_shift.start_date - datetime.timedelta(weeks=1)).responsibles.all()

		last_responsible = first_shift.responsibles.first()
		second_last_responsible = list(set(last_responsibles) - {last_responsible})[0]

		# Shuffle board members, but ensure that no one gets two shifts in a row
		shuffled_board_members = list(board_members - set(last_responsibles))
		random.shuffle(shuffled_board_members)

		print(second_last_responsible)
		print(last_responsible)

		shuffled_board_members.insert(random.randint(1, len(shuffled_board_members)), second_last_responsible)
		shuffled_board_members.insert(random.randint(2, len(shuffled_board_members)), last_responsible)

		responsibles = []
		shift_starts = []
		for shift in BoardMemberDepositShift.objects.filter(start_date__gte=first_shift.start_date):
			responsibles.append(list(shift.responsibles.all()))
			shift_starts.append(shift.start_date)

		unfilled_existing = len(shift_starts)
		assert unfilled_existing == self.WEEKS // 2

		for _ in range(self.WEEKS // self.RESPONSIBLES * len(board_members)):
			responsibles.append([])
			shift_starts.append(next_deposit_shift_start(shift_starts[-1]))

		for s, _ in enumerate(shift_starts):
			first_index = (s - unfilled_existing) // (self.WEEKS // 2)
			if first_index >= 0:
				responsibles[s].append(shuffled_board_members[first_index])

			if first_index + 1 < len(board_members):
				responsibles[s].append(shuffled_board_members[first_index + 1])
				assert len(responsibles[s]) == self.RESPONSIBLES
			else:
				assert len(responsibles[s]) == self.RESPONSIBLES // 2


			print(f'{shift_starts[s]}:')
			for bartender in responsibles[s]:
				print(f'  {bartender}')

			print()


		while True:
			r = input('Publish? [yN] ').lower()
			if r in ['', 'n']:
				return

			if r == 'y':
				break

		print()
		print('Publishing...')

		period = BoardMemberDepositShiftPeriod.objects.create()

		for s, d in enumerate(shift_starts):
			if s < unfilled_existing:
				shift = BoardMemberDepositShift.objects.get(start_date=d)
			else:
				shift = BoardMemberDepositShift.objects.create(start_date=d,
			                                                   period=period)

			shift.responsibles.set(responsibles[s])
			shift.save()
