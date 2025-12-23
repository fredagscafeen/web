import datetime

from django.conf import settings
from django.utils import timezone

from reminder.management.commands._private import ReminderCommand
from udlejning.models import Udlejning


class Command(ReminderCommand):
    help = "Sends rental reminders to responsible board members"

    def get_next_events(self):
        return Udlejning.objects.filter(
            dateFrom__gte=timezone.now(),
            dateFrom__lte=timezone.now() + datetime.timedelta(7),
        )

    def get_bartenders_from_event(self, event):
        return event.bartendersInCharge.all()

    def email_subject(self, humanized_bartenders, event):
        return f"Du er ansvarlig for et event i denne uge!"

    def email_body(self, humanized_bartenders, event):
        return f"""Hej {humanized_bartenders}.

Du/I er ansvarlige for at leje {event.draftBeerSystem} ud til {event.whoReserved}, d. {event.dateFrom.strftime("%d. %B %H:%M:%S")}.

Husk at sætte det til strøm mindst 12 timer inden arrangementet.

/snek"""

    def email_cc(self):
        return [f"udlejning@{settings.DOMAIN}"]

    def email_reply_to(self):
        return []
