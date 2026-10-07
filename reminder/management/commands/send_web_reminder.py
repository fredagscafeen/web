import datetime

from constance import config
from django.conf import settings
from django.utils import timezone

from bartenders.models import (
    BartenderShift,
    BoardMember,
    BoardMemberDepositShift,
    BoardMemberPeriod,
)
from fredagscafeen.email import send_template_email
from reminder.management.commands._private import BaseCommand

WEEKS_TO_CONSIDER_SOON = 4


class Command(BaseCommand):
    help = "Send web reminder email to responsible board member"

    def handle(self, *args, **options):
        if not config.SEND_REMINDERS:
            print("SEND_REMINDERS is false, not sending any reminders.")
            return

        weeks_generated_at_a_time = get_weeks_generated_at_a_time()

        bartenderShift_info = get_bartender_shift_info(weeks_generated_at_a_time)
        depositShift_info = get_deposit_shift_info(weeks_generated_at_a_time)

        body_template = f"""Dette er en automatisk email.

{bartenderShift_info}{depositShift_info}

/snek"""

        subject = ""
        if bartenderShift_info == "" and depositShift_info == "":
            print(
                f"All bar and deposit shifts are generated for the next {WEEKS_TO_CONSIDER_SOON} weeks. No reminder sent."
            )
            return
        if bartenderShift_info != "" and depositShift_info != "":
            subject = f"VIGTIGT: Husk at generere barvagter og pantvagter for de næste {weeks_generated_at_a_time} uger!"
        elif bartenderShift_info != "":
            subject = f"VIGTIGT: Husk at generere barvagter for de næste {weeks_generated_at_a_time} uger!"
        elif depositShift_info != "":
            subject = f"VIGTIGT: Husk at generere pantvagter for de næste {weeks_generated_at_a_time} uger!"

        send_template_email(
            subject=subject,
            body_template=body_template,
            to=[f"web@{settings.DOMAIN}"],
            cc=[f"reminder@{settings.DOMAIN}"],
            reply_to=[f"best@{settings.DOMAIN}"],
        )

        print(f"Reminder sent to the web mailing list!")


def get_weeks_generated_at_a_time():
    current_board_member_period = BoardMemberPeriod.objects.filter(
        start_date__lte=timezone.now()
    ).first()
    if current_board_member_period is None:
        print(
            "No current board member period found. Please create a board member period first."
        )
        return 0
    active_board_members = BoardMember.objects.filter(
        period=current_board_member_period, bartender__isActiveBartender=True
    ).count()
    return (
        active_board_members * 2
    )  # Assuming each board member is responsible for 2 weeks of shifts per generation cycle


def get_bartender_shift_info(weeks_generated_at_a_time):
    futureBartenderShifts = BartenderShift.objects.filter(
        start_datetime__gte=timezone.now()
    )
    bartenderShift_info = ""
    if futureBartenderShifts is None:
        bartenderShift_info += f"""
    Der er ingen barvagter genereret til den kommende periode. Husk at generere barvagter for de næste {weeks_generated_at_a_time} uger.
    """
    else:
        if futureBartenderShifts.count() < WEEKS_TO_CONSIDER_SOON:
            if futureBartenderShifts.count() == 1:
                bartenderShift_info += f"""
    Der er kun barvagter genereret for den næste uge. Husk at generere barvagter for de næste {weeks_generated_at_a_time} uger.
    """
            else:
                bartenderShift_info += f"""
    Der er kun barvagter genereret for de næste {futureBartenderShifts.count()} uger. Husk at generere barvagter for de næste {weeks_generated_at_a_time} uger.
    """
    return bartenderShift_info


def get_deposit_shift_info(weeks_generated_at_a_time):
    futureDepositShifts = BoardMemberDepositShift.objects.filter(
        start_date__gte=timezone.now()
    )
    depositShift_info = ""
    if futureDepositShifts is None:
        depositShift_info += f"""
    Der er ingen pantvagter genereret til den kommende periode. Husk at generere pantvagter for de næste {weeks_generated_at_a_time} uger.
    """
    else:
        if futureDepositShifts.count() < WEEKS_TO_CONSIDER_SOON:
            if futureDepositShifts.count() == 1:
                depositShift_info += f"""
    Der er kun pantvagter genereret for den næste uge. Husk at generere pantvagter for de næste {weeks_generated_at_a_time} uger.
    """
            else:
                depositShift_info += f"""
    Der er kun pantvagter genereret for de næste {futureDepositShifts.count()} uger. Husk at generere pantvagter for de næste {weeks_generated_at_a_time} uger.
    """
    return depositShift_info
