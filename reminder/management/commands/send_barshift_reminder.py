import datetime
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from bartenders.models import BartenderShift
from reminder.management.commands._private import ReminderCommand


class Command(ReminderCommand):
    help = 'Send barshift reminder emails to bartenders for the upcoming friday'

    def get_next_event(self):
        return BartenderShift.objects.filter(end_datetime__gte=timezone.now(),
                                             end_datetime__lte=timezone.now() + datetime.timedelta(7)).first()

    def get_bartender_usernames_from_event(self, event):
        return [b.username for b in event.all_bartenders()]

    def send_reminder_email(self, bartenders):
        subject = 'You have a barshift this friday!'
        humanize_bartenders = self.humanize_bartenders(bartenders)

        context = {'content':
                       'Hello ' + humanize_bartenders + '.\n' \
                       + '\n' \
                         'The coming Friday it is YOUR turn to run Fredagscafeen.\n' \
                         'This is an automated mail sent to you as well as to Bestyrelsen.\n' \
                         'It is primarily sent so that you may arrange for someone else to take your shift, ' \
                         'but it also serves as a kind reminder :)\n' \
                         'Remember that your shift starts at 14:30.\n' \
                         '\n' \
                         'See you at the bar!\n' \
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
            reply_to=['alle@fredagscafeen.dk'])
        email.attach_alternative(body_html, 'text/html')
        email.send()
        print('Reminders sent to ' + humanize_bartenders + '!')
