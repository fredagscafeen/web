import datetime
import random
from itertools import chain, zip_longest

from django.core.management.base import BaseCommand, CommandError

from bartenders.models import (
    Bartender,
    BoardMember,
    BoardMemberDepositShift,
    BoardMemberDepositShiftPeriod,
    next_deposit_shift_start,
)


class Command(BaseCommand):
    help = "Generates new deposit shifts"

    RESPONSIBLES = int(input("Number of responsible board members (2): ") or "2")
    WEEKS = int(input("Number of consecutive weeks (2): ") or "2")

    def handle(self, *args, **options):
        board_members = set(b for b in Bartender.objects.all() if b.isBoardMember)

        for shift in iter(BoardMemberDepositShift.objects.all()):
            first_shift = shift

        assert first_shift != None

        last_responsible = None
        for board_member in board_members:
            last_responsible = board_member

        assert last_responsible != None
        second_last_responsible = list(set(board_members) - {last_responsible})[0]

        # Shuffle board members, but ensure that no one gets two shifts in a row
        shuffled_board_members = list(board_members)
        random.shuffle(shuffled_board_members)

        if second_last_responsible.isBoardMember:
            shuffled_board_members.insert(
                random.randint(1, len(shuffled_board_members)), second_last_responsible
            )

        if last_responsible.isBoardMember:
            shuffled_board_members.insert(
                random.randint(2, len(shuffled_board_members)), last_responsible
            )

        print("Shuffled ordering of board members:")
        print(*shuffled_board_members, sep="\n")
        print()

        responsibles = []
        shift_starts = []
        for shift in BoardMemberDepositShift.objects.filter(
            start_date__gte=first_shift.start_date
        ):
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

            print(f"{shift_starts[s]}:")
            for bartender in responsibles[s]:
                print(f"  {bartender}")

            print()

        while True:
            r = input("Publish? [y/N] ").lower()
            if r in ["", "n"]:
                return

            if r == "y":
                break

        print()
        print("Publishing...")

        period = BoardMemberDepositShiftPeriod.objects.create()

        for s, d in enumerate(shift_starts):
            if s < unfilled_existing:
                shift = BoardMemberDepositShift.objects.get(start_date=d)
            else:
                shift = BoardMemberDepositShift.objects.create(
                    start_date=d, period=period
                )

            shift.responsibles.set(responsibles[s])
            shift.save()
