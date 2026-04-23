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
This command generates deposit shifts for active board members using the two most recent filled shifts as seed data.
It detects members with back-to-back shifts, determines a next-in-line member, shuffles board members, moves recent responsibles to the back, and then assigns each shift using a staggered sliding index.

Arguments:
- --responsibles: number of responsible board members per shift.
- --weeks: consecutive-week target used to compute cycle count.

The command creates:
    total_shifts = ceil(weeks / responsibles_per_shift) * number_of_active_board_members

After previewing the generated schedule, it asks for confirmation before publishing to the database.
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

        if weeks < 1:
            raise CommandError("--weeks must be at least 1")

        if responsibles_per_shift < 1:
            raise CommandError("--responsibles must be at least 1")

        if responsibles_per_shift > len(board_members):
            raise CommandError(
                "--responsibles cannot be greater than number of active board members"
            )

        last_two_filled_shifts = list(
            BoardMemberDepositShift.objects.filter(responsibles__isnull=False)
            .distinct()
            .order_by("-start_date")[:2]
        )

        if len(last_two_filled_shifts) == 0:
            raise CommandError("No existing deposit shifts with responsibles found")

        last_shift = last_two_filled_shifts[0]
        second_last_shift = (
            last_two_filled_shifts[1] if len(last_two_filled_shifts) > 1 else None
        )

        last_responsibles = [
            bartender
            for bartender in last_shift.responsibles.all()
            if bartender in board_members
        ]
        second_last_responsibles = []
        if second_last_shift is not None:
            second_last_responsibles = [
                bartender
                for bartender in second_last_shift.responsibles.all()
                if bartender in board_members
            ]

        repeated_from_last_two = [
            bartender
            for bartender in last_responsibles
            if bartender in second_last_responsibles
        ]

        next_in_line = None
        if second_last_shift is not None:
            next_candidates = [
                bartender
                for bartender in last_responsibles
                if bartender not in second_last_responsibles
            ]
            if len(next_candidates) > 0:
                next_in_line = next_candidates[0]

        if next_in_line is None and len(last_responsibles) > 0:
            next_in_line = last_responsibles[0]

        # Shuffle board members and move recent responsibles from the last two shifts to the back.
        shuffled_board_members = list(board_members)
        random.shuffle(shuffled_board_members)

        recent_responsibles = []
        for bartender in second_last_responsibles + last_responsibles:
            if bartender in board_members and bartender not in recent_responsibles:
                recent_responsibles.append(bartender)

        for bartender in recent_responsibles:
            if bartender in shuffled_board_members:
                shuffled_board_members.remove(bartender)
        shuffled_board_members.extend(recent_responsibles)

        # Keep the detected next-in-line member at the front.
        if next_in_line is not None and next_in_line in shuffled_board_members:
            shuffled_board_members.remove(next_in_line)
            shuffled_board_members.insert(0, next_in_line)

        print("Shuffled ordering of board members:")
        print(*shuffled_board_members, sep="\n")
        print()

        cycles = (weeks + responsibles_per_shift - 1) // responsibles_per_shift
        total_shifts = cycles * len(board_members)

        print(
            f"Generating {total_shifts} shifts using weeks={weeks} and responsibles_per_shift={responsibles_per_shift}..."
        )
        print(f"Last shift starts on {last_shift.start_date}")
        print(f"Last shift member with two shifts in a row: {repeated_from_last_two}")
        print(f"Detected next-in-line member: {next_in_line}")
        print(f"Recent members moved to back: {recent_responsibles}")
        print()

        shift_starts = []
        d = next_deposit_shift_start(last_shift.start_date)
        for _ in range(total_shifts):
            shift_starts.append(d)
            d = next_deposit_shift_start(d)

        generated_responsibles = []
        start_index = 0
        for shift_start in shift_starts:
            shift_responsibles = []
            for offset in range(responsibles_per_shift):
                idx = (start_index + offset) % len(shuffled_board_members)
                shift_responsibles.append(shuffled_board_members[idx])

            generated_responsibles.append(shift_responsibles)

            print(f"{shift_start}:")
            for bartender in shift_responsibles:
                print(f"  {bartender}")
            print()

            start_index += 1

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
            shift, created = BoardMemberDepositShift.objects.get_or_create(
                start_date=d,
                defaults={"period": period},
            )

            if not created and shift.period is None:
                shift.period = period

            shift.responsibles.set(generated_responsibles[s])
            shift.save()
