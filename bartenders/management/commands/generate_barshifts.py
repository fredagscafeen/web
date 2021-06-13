import copy
import datetime
import random
import sys
from collections import defaultdict

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from bartenders.models import (
    Bartender,
    BartenderShift,
    BartenderShiftPeriod,
    BartenderUnavailableDate,
    next_bartender_shift_start,
)

DOUBLE_SECOND_SHIFT_START = datetime.time(23, 00)
DOUBLE_SECOND_SHIFT_DURATION = datetime.timedelta(hours=3)  # Ends at 02:00


def ceildiv(n, d):
    return ((n + 1) // d) + 1


class Command(BaseCommand):
    help = "Generate normal barshifts"

    BARTENDERS_PER_SHIFT = 4

    def add_arguments(self, parser):
        parser.add_argument("--shifts-per-bartender", type=int, default=2)
        parser.add_argument("-t", "--max-tries", type=int, default=10 ** 4)
        parser.add_argument(
            "-d",
            "--double-shift",
            action="append",
            default=[],
            type=datetime.date.fromisoformat,
        )

    def try_random_solution(
        self,
        total_shifts,
        sorted_bartenders,
        bartenders_needed,
        available_shifts,
        shifts_per_bartender,
    ):
        available_shifts = copy.deepcopy(available_shifts)

        total_needed = total_shifts * bartenders_needed
        shifts_for_bartender = [0] * len(sorted_bartenders)

        shifts = [[] for _ in range(total_shifts)]

        bartender_shifts = ceildiv(total_shifts, shifts_per_bartender)

        for i in range(bartender_shifts):
            if i == bartender_shifts - 1:
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
            return None

        # Solution is too skewed
        if min(shifts_for_bartender) + 1 < max(shifts_for_bartender):
            return None

        return shifts

    def get_shifts_score(self, bartenders, shifts, last_shifts, shifts_per_bartender):
        """
        A shifts score is based on 3 factors, with the following priorities:
        1. The amount of new bartenders, who have fewer than the normal amount of shifts.
           We want to minimize this and it should probably be possible to get this down to 0.

        2. The minimum distance between two shifts with the same bartender.
           We want to maximize this.

        3. The amount of pairs of shifts with the same bartender,
           having distance exactly equal to the distance in 2.
           We want to minize this.
        """

        last_shifts = last_shifts.copy()

        new_bartenders = set()
        new_bartender_shift_count = 0
        count = 0
        min_distance = float("inf")
        for s, bs in enumerate(shifts):
            for b in bs:
                if last_shifts[b] != None:
                    distance = s - last_shifts[b]
                    if distance < min_distance:
                        min_distance = distance
                        count = 1
                    elif distance == min_distance:
                        count += 1
                else:
                    new_bartenders.add(b)

                if b in new_bartenders:
                    new_bartender_shift_count += 1

                last_shifts[b] = s

        new_bartenders_with_fewer_shifts = (
            len(new_bartenders) * shifts_per_bartender - new_bartender_shift_count
        )

        return (new_bartenders_with_fewer_shifts, -min_distance, count)

    def get_random_solution(
        self,
        total_shifts,
        bartenders,
        bartenders_needed,
        available_shifts,
        max_tries,
        last_shifts,
        shifts_per_bartender,
    ):
        best = ((float("inf"),), None)

        sorted_bartenders = sorted(
            range(len(bartenders)), key=lambda x: len(available_shifts[x])
        )

        for bartender_i in sorted_bartenders:
            available = len(available_shifts[bartender_i])
            if available < shifts_per_bartender:
                print(
                    f"Bartender {bartenders[bartender_i]} only has {available} available dates!",
                    file=sys.stderr,
                )

        i = 0
        fails = 0
        while i < max_tries:
            result = self.try_random_solution(
                total_shifts,
                sorted_bartenders,
                bartenders_needed,
                available_shifts,
                shifts_per_bartender,
            )

            if result != None:
                i += 1
                best = min(
                    best,
                    (
                        self.get_shifts_score(
                            bartenders, result, last_shifts, shifts_per_bartender
                        ),
                        result,
                    ),
                )
            else:
                fails += 1

            best_str = f"fewer news: {best[0][0]}, min distance: {-best[0][1]}, count: {best[0][2]}"
            print(f"\r{i} / {max_tries} (failed: {fails}), best: {best_str}", end="")
            sys.stdout.flush()

        print()
        print(best_str)
        return best[1]

    def handle(self, *args, **options):
        shifts_per_bartender = options["shifts_per_bartender"]
        double_shifts = options["double_shift"]

        board_members = []
        normal_bartenders = []
        for b in Bartender.objects.filter(isActiveBartender=True):
            if b.isBoardMember:
                board_members.append(b)
            else:
                normal_bartenders.append(b)

        all_bartenders = [normal_bartenders, board_members]

        total_shifts = min(
            shifts_per_bartender * len(board_members),
            shifts_per_bartender
            * len(normal_bartenders)
            // (self.BARTENDERS_PER_SHIFT - 1),
        )

        last_shift = BartenderShift.objects.last()

        shift_start = last_shift.start_datetime
        shift_periods = []
        late_shift_indices = set()
        double_shifts_used = 0
        i = 0
        while i < total_shifts:
            i += 1
            shift_start = next_bartender_shift_start(shift_start.date())

            shift_periods.append((shift_start, None))
            if shift_start.date() in double_shifts:
                second_start_naive = datetime.datetime.combine(
                    shift_start.date(), DOUBLE_SECOND_SHIFT_START
                )
                second_start = timezone.get_default_timezone().localize(
                    second_start_naive
                )
                second_end = second_start + DOUBLE_SECOND_SHIFT_DURATION

                shift_periods[-1] = (shift_start, second_start)
                shift_periods.append((second_start, second_end))

                late_shift_indices.add(i)

                double_shifts_used += 1
                i += 1

        if i > total_shifts:
            print(
                f"WARNING: Final double shift is included, even though this means one more shift!"
            )
            total_shifts = i

        if double_shifts_used != len(double_shifts):
            print(
                f"WARNING: Only used {double_shifts_used}/{len(double_shifts)} double shifts!"
            )

        shift_indices = defaultdict(list)
        for i, (start, end) in enumerate(shift_periods):
            shift_indices[start.date()].append(i)

        print(f"Board members: {len(board_members)}")
        print(f"Other active bartenders: {len(normal_bartenders)}")
        print(
            f"Generating {total_shifts} shifts from {shift_periods[0][0].date()} to {shift_periods[-1][0].date()}"
        )

        last_shifts = []
        for bs in all_bartenders:
            l = []
            for b in bs:
                s = b.last_bartender_shift
                if s != None:
                    s = (
                        s.date - last_shift.date + datetime.timedelta(weeks=1)
                    ).days // 7 - 1
                l.append(s)
            last_shifts.append(l)

        available_shifts = [
            [set(range(total_shifts)) for _ in all_bartenders[i]] for i in range(2)
        ]

        # Could be filtered
        unavailable_dates = BartenderUnavailableDate.objects.all()

        for d in unavailable_dates:
            bartender = d.bartender

            if not bartender.isActiveBartender:
                continue

            shifts = shift_indices.get(d.date)
            if shifts == None:
                if shift_periods[0][0].date() <= d.date <= shift_periods[-1][0].date():
                    print(
                        f"WARNING: {d.date} is between first and last shift, but is not a friday"
                    )

                continue

            index = all_bartenders[bartender.isBoardMember].index(bartender)
            for shift in shifts:
                available_shifts[bartender.isBoardMember][index].remove(shift)

        for board_member, bartenders in enumerate(all_bartenders):
            for i, bartender in enumerate(bartenders):
                if bartender.prefer_only_early_shifts:
                    available_shifts[board_member][i] -= late_shift_indices

        shifts = []
        for board_member, (bartenders, ls) in enumerate(
            zip(all_bartenders, last_shifts)
        ):
            bartenders_needed = 1 if board_member else self.BARTENDERS_PER_SHIFT - 1
            shifts.append(
                self.get_random_solution(
                    total_shifts,
                    bartenders,
                    bartenders_needed,
                    available_shifts[board_member],
                    options["max_tries"],
                    ls,
                    shifts_per_bartender,
                )
            )

        print()

        shifts_for_bartender = defaultdict(int)
        for s, (start, end) in enumerate(shift_periods):
            print(f"{start}:")
            for board_member, bartenders in reversed(list(enumerate(all_bartenders))):
                for b in shifts[board_member][s]:
                    shifts_for_bartender[(board_member, b)] += 1
                    print(f"  {bartenders[b]}")

            print()

        print(f"Bartenders with fewer than {shifts_per_bartender} shifts:")
        for (board_member, b), shift_count in shifts_for_bartender.items():
            if shift_count < shifts_per_bartender:
                print(f"  {all_bartenders[board_member][b]}: {shift_count} shifts")

        print()

        print(f"Bartenders with more than {shifts_per_bartender} shifts:")
        for (board_member, b), shift_count in shifts_for_bartender.items():
            if shift_count > shifts_per_bartender:
                print(f"  {all_bartenders[board_member][b]}: {shift_count} shifts")

        print()

        while True:
            r = input("Publish? [yN] ").lower()
            if r in ["", "n"]:
                return

            if r == "y":
                break

        print()
        print("Publishing...")

        period = BartenderShiftPeriod.objects.create()

        for s, (start, end) in enumerate(shift_periods):
            responsible = all_bartenders[True][shifts[True][s][0]]
            other_bartenders = [all_bartenders[False][b] for b in shifts[False][s]]

            shift = BartenderShift.objects.create(
                start_datetime=start,
                end_datetime=end,
                responsible=responsible,
                period=period,
            )

            shift.other_bartenders.set(other_bartenders)
            shift.save()
