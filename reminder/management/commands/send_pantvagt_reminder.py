import datetime
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from bartenders.models import BoardMemberDepositShift
from reminder.management.commands._private import ReminderCommand


class Command(ReminderCommand):
    help = 'Sends email reminders to board members in charge of pant this week'

    def get_next_event(self):
        return BoardMemberDepositShift.objects.filter(end_date__gte=timezone.now(),
                                                      end_date__lte=timezone.now() + datetime.timedelta(7)).first()

    def get_bartender_usernames_from_event(self, event):
        return [b.username for b in event.responsibles.all()]

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
