import datetime

from django.conf import settings
from django.utils import timezone

from bartenders.models import BartenderShift, date_format
from events.models import CommonEvent
from reminder.management.commands._private import ReminderCommand


class Command(ReminderCommand):
    help = "Send barshift reminder emails to bartenders for the upcoming friday"

    def get_next_events(self):
        return BartenderShift.objects.filter(
            end_datetime__gte=timezone.now(),
            end_datetime__lte=timezone.now() + datetime.timedelta(7),
        )

    def get_bartenders_from_event(self, event):
        return event.all_bartenders()

    def email_subject(self, humanized_bartenders, event):
        return "Du har en barvagt på fredag!"

    def email_body(self, humanized_bartenders, event):
        start = event.start_datetime - datetime.timedelta(minutes=30)
        start_time = date_format(start, "H:i")
        common_event = CommonEvent.objects.filter(
            date=event.start_datetime.date()
        ).first()
        if common_event:
            event_info = f"""
Husk at der på fredag er {common_event.title}!
"""

        return f"""Hej {humanized_bartenders}.

Den kommende fredag er det JERES tur til at stå i Fredagscaféen.
Dette er en automatisk email sendt til jer og bestyrelsen.
Emailen er hovedsageligt sendt så I kan finde en anden at bytte vagt med,
hvis en af jer ikke har mulighed for selv at tage den.
Husk at jeres vagt starter kl. {start_time}.
{event_info}
Ses i baren!

/Bestyrelsen"""

    def email_reply_to(self):
        return [f"alle@{settings.DOMAIN}"]
