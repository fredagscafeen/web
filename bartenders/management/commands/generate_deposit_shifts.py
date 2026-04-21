import random

from django.core.management.base import BaseCommand, CommandError

from bartenders.models import (
    Bartender,
    BoardMemberDepositShift,
    BoardMemberDepositShiftPeriod,
    next_deposit_shift_start,
)


class Command(BaseCommand):
    help = "Generates new deposit shifts"

    def add_arguments(self, parser):
        parser.add_argument("--responsibles", type=int)
        parser.add_argument("--weeks", type=int)

    def handle(self, *args, **options):
        print(
            """
HELP:
This command generates new deposit shifts for board members. It ensures that no board member gets two shifts in a row, and that the last two responsible board members from the previous period are included in the new schedule.
The command will prompt you for the number of responsible board members per shift and the number of consecutive weeks to generate shifts for. After generating the schedule, it will ask for confirmation before publishing the new shifts to the database.
            """
        )

        responsibles_per_shift = options["responsibles"]
        if responsibles_per_shift is None:
            responsibles_per_shift = int(
                input("Number of responsible board members (2): ") or "2"
            )

        weeks = options["weeks"]
        if weeks is None:
            weeks = int(input("Number of consecutive weeks (2): ") or "2")

        board_members = [b for b in Bartender.objects.all() if b.isBoardMember]
        if len(board_members) < 2:
            raise CommandError(
                "Need at least 2 active board members to generate shifts"
            )

        first_shift = BoardMemberDepositShift.objects.last()
        if first_shift is None:
            raise CommandError("No existing deposit shifts found")

        previous_shift = (
            BoardMemberDepositShift.objects.filter(
                start_date__lt=first_shift.start_date,
                responsibles__isnull=False,
            )
            .distinct()
            .last()
        )

        previous_responsibles = []
        if previous_shift is not None:
            previous_responsibles = [
                bartender
                for bartender in previous_shift.responsibles.all()
                if bartender in board_members
            ]

        # Shuffle board members, but ensure that no one gets two shifts in a row
        shuffled_board_members = list(board_members)
        random.shuffle(shuffled_board_members)

        # Keep the previous shift's responsibles at the front without duplicating entries.
        for bartender in reversed(previous_responsibles):
            if bartender in shuffled_board_members:
                shuffled_board_members.remove(bartender)
                shuffled_board_members.insert(0, bartender)

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
        assert unfilled_existing == weeks // 2

        for _ in range(weeks // responsibles_per_shift * len(board_members)):
            responsibles.append([])
            shift_starts.append(next_deposit_shift_start(shift_starts[-1]))

        for s, _ in enumerate(shift_starts):
            first_index = (s - unfilled_existing) // (weeks // 2)
            if first_index >= 0:
                candidate = shuffled_board_members[first_index]
                if candidate not in responsibles[s]:
                    responsibles[s].append(candidate)

            if first_index + 1 < len(board_members):
                candidate = shuffled_board_members[first_index + 1]
                if candidate in responsibles[s]:
                    candidate = None
                    for bartender in shuffled_board_members[first_index + 2 :]:
                        if bartender not in responsibles[s]:
                            candidate = bartender
                            break

                if candidate is not None and candidate not in responsibles[s]:
                    responsibles[s].append(candidate)

                assert len(responsibles[s]) == responsibles_per_shift
            else:
                assert len(responsibles[s]) == responsibles_per_shift // 2

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
