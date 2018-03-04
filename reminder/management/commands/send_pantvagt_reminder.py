from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from reminder.management.commands._private import ReminderCommand


class Command(ReminderCommand):
    help = 'Sends email reminders to board members in charge of pant this week'

    storage = 'pantvagt_reminder.calendar.storage'
    calendar_id = '2a157v77f7uuvm5f41ifbfna5s@group.calendar.google.com'
    summary_offset = 0

    def send_reminder_email(self, bartenders):
        humanize_bartenders = self.humanize_bartenders(bartenders)

        subject = 'Hello ' + humanize_bartenders + '. You have to take care of the pant this week!'
        context = {'content':
                       'Hello ' + humanize_bartenders + '.\n' \
                       + '\n' \
                         'You have to take care of the pant this week!\n' \
                         '\n' \
                         '/Bestyrelsen'}

        body_text = render_to_string('email.txt', context)
        body_html = render_to_string('email.html', context)
        recipient_list = self.filter_with_warning(bartenders)

        email = EmailMultiAlternatives(
            subject=subject,
            body=body_text,
            from_email='best@fredagscafeen.dk',
            to=recipient_list,
            cc=['best@fredagscafeen.dk'],
            reply_to=['best@fredagscafeen.dk'])
        email.attach_alternative(body_html, 'text/html')
        email.send()
        print('Reminders sent to ' + humanize_bartenders + '!')
