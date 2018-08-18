import datetime
from django.utils import timezone

from bartenders.models import BoardMemberDepositShift
from reminder.management.commands._private import ReminderCommand


class Command(ReminderCommand):
    help = 'Sends email reminders to board members in charge of pant this week'

    def get_next_events(self):
        return BoardMemberDepositShift.objects.filter(end_date__gte=timezone.now(),
                                                      end_date__lte=timezone.now() + datetime.timedelta(7))

    def get_bartenders_from_event(self, event):
        return event.responsibles.all()

    def email_subject(self, humanized_bartenders, event):
        return f'Du har pantvagt i denne uge!'

    def email_body(self, humanized_bartenders, event):
        return f'''Hej {humanized_bartenders}.

I skal tage jer af panten i denne uge!

/Bestyrelsen'''

    def email_reply_to(self):
        return ['best@fredagscafeen.dk']
