from django.core.mail import send_mail
from django.core.management import BaseCommand
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from fredagscafeen.email import send_template_email


class ReminderCommand(BaseCommand):
    """ Superclass that encapsulates logic related to sending reminder emails """

    def handle(self, *args, **options):
        event = self.get_next_event()

        if not event:
            print('No upcoming events found.')
            return

        bartenders = self.get_bartenders_from_event(event)
        self.send_reminder_email(bartenders)

    def send_reminder_email(self, bartenders):
        humanized_bartenders = self.humanized_bartenders(bartenders)

        send_template_email(
			subject=self.email_subject(humanized_bartenders),
			body_template=self.email_body(humanized_bartenders),
			text_format={},
			html_format={},
			to=self.filter_with_warning(bartenders),
            cc=['best@fredagscafeen.dk'],
            reply_to=self.email_reply_to()
		)

        print(f'Reminders sent to {", ".join(f"{b.name} ({b.email})" for b in bartenders if b.email)}!')

    def humanized_bartenders(self, bartenders):
        humanized_bartenders = ''
        for i, bartender in enumerate(bartenders):
            humanized_bartenders += f'{bartender.name} ({bartender.username})'
            if i == len(bartenders) - 2:
                humanized_bartenders += ' og '
            if i < len(bartenders) - 2:
                humanized_bartenders += ', '
        return humanized_bartenders

    def filter_with_warning(self, bartenders):
        recipient_list = []
        for bartender in bartenders:
            if not bartender.email:
                self.send_warning(bartender)
            else:
                recipient_list.append(bartender.email)

        return recipient_list

    def send_warning(self, bartender):
        warning = f'WARNING: Could not find e-mail for bartender {bartender}! Bartender did not get a reminder!'
        send_mail(subject=warning,
                  recipient_list=['best@fredagscafeen.dk'],
                  from_email='best@fredagscafeen.dk',
                  message=warning)

    def get_next_event(self):
        raise NotImplementedError

    def get_bartenders_from_event(self, event):
        raise NotImplementedError

    def email_subject(self, humanized_bartenders):
        raise NotImplementedError

    def email_body(self, humanized_bartenders):
        raise NotImplementedError

    def email_reply_to(self):
        raise NotImplementedError

