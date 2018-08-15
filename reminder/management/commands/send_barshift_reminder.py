import datetime
from django.utils import timezone

from bartenders.models import BartenderShift
from reminder.management.commands._private import ReminderCommand


class Command(ReminderCommand):
    help = 'Send barshift reminder emails to bartenders for the upcoming friday'

    def get_next_events(self):
        return BartenderShift.objects.filter(end_datetime__gte=timezone.now(),
                                             end_datetime__lte=timezone.now() + datetime.timedelta(7))

    def get_bartenders_from_event(self, event):
        return event.all_bartenders()

    def email_subject(self, humanized_bartenders):
        return 'Du har en barvagt på fredag!'

    def email_body(self, humanized_bartenders):
        return f'''Hej {humanized_bartenders}.

Den kommende fredag er det DIN tur til at stå i Fredagscaféen.
Dette er en automatisk email sendt til jer og bestyrelsen.
Emailen er hovedsageligt sendt så du kan finde en anden at bytte vagt med,
hvis du ikke har mulighed for selv at tage den.
Husk at din vagt starter kl. 14:30.

Ses i baren!

/Bestyrelsen'''

    def email_reply_to(self):
        return ['alle@fredagscafeen.dk']
