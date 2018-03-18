from django.core.mail import send_mail
from django.core.management import BaseCommand

from bartenders.models import Bartender


class ReminderCommand(BaseCommand):
    """ Superclass that encapsulates logic related to sending reminder emails """

    def handle(self, *args, **options):
        event = self.get_next_event()

        if not event:
            print('No upcoming events found.')
            return

        bartenders = self.get_bartender_usernames_from_event(event)
        bartenders_with_emails = []
        for bartender in bartenders:
            try:
                bartender = Bartender.objects.get(username=bartender)
                bartenders_with_emails.append((bartender.username, bartender.email))
            except Bartender.DoesNotExist:
                bartenders_with_emails.append((bartender, ''))
        self.send_reminder_email(bartenders_with_emails)
        print(bartenders_with_emails)

    def humanize_bartenders(self, bartenders):
        humanize_bartenders = ''
        for i, bartender in enumerate(bartenders):
            humanize_bartenders += bartender[0]
            if i == len(bartenders) - 2:
                humanize_bartenders += ' and '
            if i < len(bartenders) - 2:
                humanize_bartenders += ', '
        return humanize_bartenders

    def filter_with_warning(self, bartenders):
        recipient_list = []
        for bartender in bartenders:
            if bartender[1] == '':
                self.send_warning(bartender[0])
            recipient_list.append(bartender[1])
        return recipient_list

    def send_warning(self, bartender):
        warning = 'WARNING: Could not find e-mail for bartender ' + bartender + '! Bartender did not get a reminder!'
        send_mail(subject=warning,
                  recipient_list=['best@fredagscafeen.dk'],
                  from_email='datcafe@gmail.com',
                  message=warning)

    def get_next_event(self):
        raise NotImplementedError

    def get_bartender_usernames_from_event(self, event):
        raise NotImplementedError

    def send_reminder_email(self, bartenders):
        raise NotImplementedError