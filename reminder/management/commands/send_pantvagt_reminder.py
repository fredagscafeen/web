from __future__ import print_function

import httplib2
import os

from django.core.mail import send_mail, EmailMessage
from django.core.management import BaseCommand
from googleapiclient import discovery

import oauth2client
from oauth2client import client
from oauth2client import tools
from oauth2client import file

import datetime

from bartenders.models import Bartender


SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Google Calendar API Python Quickstart'


def get_credentials():
    flags = tools.argparser.parse_args(args=['--noauth_local_webserver'])
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir)
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    store = oauth2client.file.Storage('pantvagt_reminder.calendar.storage')
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = oauth2client.client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        print(flow)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = oauth2client.tools.run_flow(flow, store, flags)
        print('Storing credentials to ' + 'pantvagt_reminder.calendar.storage')
    return credentials


def get_bartenders_from_event(event):
    event_string = event['summary'].split(' ')
    bartenders = []
    for x in event_string:
        if x != '-' and x != '+':
            bartenders.append(x)
    return bartenders


def send_warning(bartender):
    warning = 'WARNING: Could not find e-mail for bartender ' + bartender + '! Bartender did not get a reminder!'
    print(warning)
    send_mail(subject=warning,
              recipient_list=['best@fredagscafeen.dk'],
              from_email='datcafe@gmail.com',
              message=warning
              )


class Command(BaseCommand):
    def __init__(self):
        super(Command, self).__init__()

    def handle(self, *args, **options):
        credentials = get_credentials()
        http = credentials.authorize(httplib2.Http())
        service = discovery.build('calendar', 'v3', http=http)
        pantvagter_calendar_id = '2a157v77f7uuvm5f41ifbfna5s@group.calendar.google.com'
        now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        events_results = service.events().list(
            calendarId=pantvagter_calendar_id, timeMin=now, maxResults=1, singleEvents=True,
            orderBy='startTime').execute()
        events = events_results.get('items', [])

        if not events:
            print('No upcoming events found.')
        for event in events:
            bartenders = get_bartenders_from_event(event)
            print(bartenders)
            bartenders_with_emails = []
            for bartender in bartenders:
                try:
                    bartender = Bartender.objects.get(username=bartender)
                    bartenders_with_emails.append((bartender.username, bartender.email))
                except Bartender.DoesNotExist:
                    bartenders_with_emails.append((bartender, ''))
            print(bartenders_with_emails)
            send_reminder_email(bartenders_with_emails)


def send_reminder_email(bartenders):
    humanize_bartenders = ''
    for i, bartender in enumerate(bartenders):
        humanize_bartenders += bartender[0]
        if i < len(bartenders) - 2:
            humanize_bartenders += ', '
        if i == len(bartenders) - 2:
            humanize_bartenders += ' and '

    subject = 'Hello ' + humanize_bartenders + '. You have to take care of the pant this week!'
    message = 'Hello ' + humanize_bartenders + '.\n' \
              + '\n' \
                'You have to take care of the pant this week!\n' \
                '\n' \
                '/Bestyrelsen'
    from_email = 'best@fredagscafeen.dk'
    reply_to = ['best@fredagscafeen.dk']
    recipient_list = []
    for bartender in bartenders:
        if bartender[1] == '':
            send_warning(bartender[0])
        recipient_list.append(bartender[1])
    email = EmailMessage(
        subject=subject,
        body=message,
        from_email=from_email,
        to=recipient_list,
        cc=['best@fredagscafeen.dk'],
        reply_to=reply_to)
    email.send()
    print('Reminders sent to ' + humanize_bartenders + '!')
