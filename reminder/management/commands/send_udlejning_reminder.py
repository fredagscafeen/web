import datetime

from django.utils import timezone

from reminder.management.commands._private import ReminderCommand
from udlejning.models import Udlejning


class Command(ReminderCommand):
    help = "Sends email reminders to board members about rentals this week"

    def get_next_events(self):
        return Udlejning.objects.filter(
            end_date__gte=timezone.now(),
            end_date__lte=timezone.now() + datetime.timedelta(7),
        )

    def get_bartenders_from_event(self, event):
        return event.bartendersInCharge.all()

    def email_subject(self, humanized_bartenders, event):
        return f"Der er udlejninger i denne uge!"

    def email_body(self, humanized_bartenders, event):
        return f"""Hej {humanized_bartenders}.

I skal tage jer af panten i denne uge!

/Bestyrelsen"""

    def email_reply_to(self):
        return ["best@fredagscafeen.dk"]
