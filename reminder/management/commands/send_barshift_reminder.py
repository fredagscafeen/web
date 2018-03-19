import datetime
from django.utils import timezone

from bartenders.models import BartenderShift
from reminder.management.commands._private import ReminderCommand


class Command(ReminderCommand):
    help = 'Send barshift reminder emails to bartenders for the upcoming friday'

    def get_next_event(self):
        return BartenderShift.objects.filter(end_datetime__gte=timezone.now(),
                                             end_datetime__lte=timezone.now() + datetime.timedelta(7)).first()

    def get_bartenders_from_event(self, event):
        return event.all_bartenders()

    def email_subject(self, humanized_bartenders):
        return 'You have a barshift this friday!'

    def email_body(self, humanized_bartenders):
        return f'''Hello {humanized_bartenders}.

The coming Friday it is YOUR turn to run Fredagscafeen.
This is an automated mail sent to you as well as to Bestyrelsen.
It is primarily sent so that you may arrange for someone else to take your shift, but it also serves as a kind reminder :)
Remember that your shift starts at 14:30.

See you at the bar!

/Bestyrelsen'''

    def email_reply_to(self):
        return ['alle@fredagscafeen.dk']