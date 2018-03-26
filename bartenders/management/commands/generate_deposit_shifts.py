from django.core.management.base import BaseCommand, CommandError
from bartenders.models import Bartender, BoardMember, BoardMemberDepositShift, BoardMemberDepositShiftPeriod, next_deposit_shift_start
import random
from itertools import zip_longest, chain


# masv is missing as he has been assigned
NEW_USERNAMES = '''
baaden
Old
Warumdk
drewsen
alberte
'''


class Command(BaseCommand):
	help = 'Generates new deposit shifts'

	RESPONSIBLES = 2
	WEEKS = 4

	def handle(self, *args, **options):
		# TODO: This needs to be updated at next generation
		new_usernames = NEW_USERNAMES.strip().splitlines()

		board_members = list(Bartender.objects.filter(boardmember__isnull=False).exclude(username='masv'))
		new_board_members = list(Bartender.objects.filter(username__in=new_usernames))
		old_board_members = [b for b in board_members if b not in new_board_members]

		print(f'New board members: {len(new_board_members)}')
		print(f'Old board members: {len(old_board_members)}')

		first_shift = None
		for shift in reversed(BoardMemberDepositShift.objects.all()):
			if shift.responsibles.count() == self.RESPONSIBLES:
				break

			first_shift = shift


		assert first_shift != None

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


		random.shuffle(new_board_members)
		random.shuffle(old_board_members)

		for s in range(len(shift_starts)):
			responsibles[s].append(new_board_members[s // self.WEEKS])

			if unfilled_existing <= s < len(shift_starts) - unfilled_existing:
				responsibles[s].append(old_board_members[(s - unfilled_existing) // self.WEEKS])
				assert len(responsibles[s]) == self.RESPONSIBLES

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
