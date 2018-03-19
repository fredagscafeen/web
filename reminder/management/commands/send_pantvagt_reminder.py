import datetime
from django.utils import timezone

from bartenders.models import BoardMemberDepositShift
from reminder.management.commands._private import ReminderCommand


class Command(ReminderCommand):
    help = 'Sends email reminders to board members in charge of pant this week'

    def get_next_event(self):
        return BoardMemberDepositShift.objects.filter(end_date__gte=timezone.now(),
                                                      end_date__lte=timezone.now() + datetime.timedelta(7)).first()

    def get_bartenders_from_event(self, event):
        return event.responsibles.all()

    def email_subject(self, humanized_bartenders):
        return f'Hello {humanized_bartenders}. You have to take care of the pant this week!'

    def email_body(self, humanized_bartenders):
        return f'''Hello {humanized_bartenders}.

You have to take care of pant this week!

/Bestyrelsen'''

    def email_reply_to(self):
        return ['best@fredagscafeen.dk']