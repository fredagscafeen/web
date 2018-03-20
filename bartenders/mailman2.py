from requests_html import HTMLSession

class MailmanError(Exception):
	pass

class AuthenticationError(MailmanError):
	pass

class OperationError(MailmanError):
	pass

class Mailman:
	'''
	Class for interacting with Mailman 2 lists.
	Tested on version 2.1.15

	Requires that the list language is English (USA)
	and that admin_member_chunksize is >= the number of subscribers.
	'''

	NEED_AUTHENTICATION_TITLE_SUFFIX = 'Administrator Authentication'

	SUBSCRIBED_SUCCESSFULLY = 'Successfully subscribed:'
	UNSUBSCRIBED_SUCCESSFULLY = 'Successfully Unsubscribed:'

	LOGIN_URL = ''
	LIST_URL = '/members'
	ADD_URL = '/members/add'
	REMOVE_URL = '/members/remove'

	def __init__(self, url_base, name, password):
		self.url_prefix = f'{url_base}/admin/{name}'
		self.password = password
		self.session = HTMLSession()

		self._login()

	def _login(self):
		login_url = self.url_prefix + self.LOGIN_URL
		r = self.session.post(login_url, data={'adminpw': self.password})
		if r.status_code == 401:
			raise AuthenticationError('Couldn\'t login with password')
		elif not r.ok:
			raise OperationError(f'Got unknown status {r.status_code} while trying to login')

	def _request(self, request_fun, url, *args, **kwargs):
		url = self.url_prefix + url

		first_try = True
		while True:
			r = request_fun(url, *args, **kwargs)
			title_el = r.html.find('title', first=True)
			if title_el and title_el.text.endswith(self.NEED_AUTHENTICATION_TITLE_SUFFIX):
				if not first_try:
					raise AuthenticationError('Login session doesn\'t seem to work')

				self._login()
			else:
				return r

			first_try = False

	def _get(self, *args, **kwargs):
		return self._request(self.session.get, *args, **kwargs)

	def _post(self, *args, **kwargs):
		return self._request(self.session.post, *args, **kwargs)

	def _get_csrf_token(self, url):
		r = self._get(url)
		if not r.ok:
			raise OperationError(f'Got unknown status {r.status_code} while trying to get csrf token')

		csrf_token_el = r.html.find('[name="csrf_token"]', first=True)
		if not csrf_token_el:
			raise OperationError(f'Couldn\'t find crsf token element')

		return csrf_token_el.attrs['value']

	def _post_form(self, url, data):
		csrf_token = self._get_csrf_token(url)
		r = self._post(url, data={**data, 'csrf_token': csrf_token})
		if not r.ok:
			raise OperationError(f'Got unknown status {r.status_code} while trying to post form')

		for sel in ['h5', 'h3']:
			result_el = r.html.find(sel, first=True)
			if result_el:
				break
		else:
			raise OperationError(f'Couldn\'t get result from posting form')

		return result_el.text

	def get_subscribers(self):
		r = self._get(self.LIST_URL)
		if not r.ok:
			raise OperationError(f'Got unknown status {r.status_code} while trying to get list of subscribers')

		subscriber_links = r.html.find('a[href*="options"]')
		return [l.text for l in subscriber_links]

	def add_subscriptions(self, emails, invite=False, send_welcome=True, notify_owner=False):
		result = self._post_form(self.ADD_URL, {
			'subscribe_or_invite': int(invite),
			'send_welcome_msg_to_this_batch': int(send_welcome),
			'send_notifications_to_list_owner': int(notify_owner),
			'subscribees': '\n'.join(emails),
		})

		if result != self.SUBSCRIBED_SUCCESSFULLY:
			raise OperationError(f'Got unknown response: {result}')

	def remove_subscriptions(self, emails, confirm=False, notify_owner=False):
		result = self._post_form(self.REMOVE_URL, {
			'send_unsub_ack_to_this_batch': int(confirm),
			'send_unsub_notifications_to_list_owner': int(notify_owner),
			'unsubscribees': '\n'.join(emails),
		})

		if result != self.UNSUBSCRIBED_SUCCESSFULLY:
			raise OperationError(f'Got unknown response: {result}')
