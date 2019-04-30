from django.contrib.auth.models import User
from bartenders.models import Bartender
from bartab.models import BarTabUser

from .models import EmailToken

class EmailTokenBackend:
	@classmethod
	def has_exactly_one(self, model, email):
		try:
			model.objects.get(email=email)
			return True
		except (model.DoesNotExist, model.MultipleObjectsReturned):
			return False

	@classmethod
	def is_bartender(self, email):
		return self.has_exactly_one(Bartender, email)

	@classmethod
	def is_bartab_user(self, email):
		return self.has_exactly_one(BarTabUser, email)

	@classmethod
	def is_user(self, email):
		return self.has_exactly_one(User, email) or self.is_bartender(email) or self.is_bartab_user(email)

	def authenticate(self, request, email=None, token=None):
		try:
			email_token = EmailToken.objects.get(email=email, token=token)
		except EmailToken.DoesNotExist:
			return None

		email_token.refresh_token()

		try:
			user = User.objects.get(email=email, is_staff=True)
		except User.DoesNotExist:
			user, _ = User.objects.get_or_create(email=email, defaults={
				'username': f'ZZZZZ_email_{email}' # Z is lexicographically large
			})

		return user

	def get_user(self, user_id):
		try:
			return User.objects.get(pk=user_id)
		except User.DoesNotExist:
			return None
