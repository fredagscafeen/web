import os
from datetime import datetime

import httplib2
import oauth2client
from django.core.mail import send_mail
from django.core.management import BaseCommand
from googleapiclient import discovery
from oauth2client import file, client, tools

from bartenders.models import Bartender

SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Google Calendar API Python Quickstart'


def get_credentials(storage):
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
	store = oauth2client.file.Storage(storage)
	credentials = store.get()
	if not credentials or credentials.invalid:
		flow = oauth2client.client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
		print(flow)
		flow.user_agent = APPLICATION_NAME
		if flags:
			credentials = oauth2client.tools.run_flow(flow, store, flags)
		print('Storing credentials to ' + storage)
	return credentials


def get_next_event(credentials, calendar_id):
	http = credentials.authorize(httplib2.Http())
	service = discovery.build('calendar', 'v3', http=http)
	barvagter_calendar_id = calendar_id
	now = datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
	events_results = service.events().list(
		calendarId=barvagter_calendar_id, timeMin=now, maxResults=1, singleEvents=True,
		orderBy='startTime').execute()
	events = events_results.get('items', [])
	return events[0] if events else None


def get_bartenders_from_event(event, offset):
	event_string = event['summary'].split(' ')[offset:]
	return [x for x in event_string if x not in ('-', '+')]


class ReminderCommand(BaseCommand):
	""" Superclass that encapsulates logic related to sending reminder emails """

	storage = None
	calendar_id = None
	summary_offset = None

	def handle(self, *args, **options):
		credentials = get_credentials(self.storage)
		event = get_next_event(credentials, self.calendar_id)

		if not event:
			print('No upcoming events found.')
			return

		bartenders = get_bartenders_from_event(event, offset=self.summary_offset)
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

	def send_reminder_email(self, bartenders):
		raise NotImplemented