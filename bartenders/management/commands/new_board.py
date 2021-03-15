import datetime
import secrets

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from bartenders.models import BoardMember, BoardMemberPeriod

User = get_user_model()


def str_to_date(s):
    return datetime.datetime.strptime(s, "%Y-%m-%d").date()


class Command(BaseCommand):
    help = "Run after the General Meeting"

    def add_arguments(self, parser):
        parser.add_argument("--start-date", type=str_to_date, required=True)

    def handle(self, *args, **options):
        previous_period = BoardMemberPeriod.get_current_period()
        previous_board_members = BoardMember.objects.filter(period=previous_period)

        period = BoardMemberPeriod.objects.create(start_date=options["start_date"])

        for bm in previous_board_members:
            BoardMember.objects.create(
                bartender=bm.bartender,
                period=period,
                title=bm.title,
                responsibilities=bm.responsibilities,
                image=bm.image,
            )

        print(
            "Created a new board member period. Remember to add/remove people in the admin interface."
        )
