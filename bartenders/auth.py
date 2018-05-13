from django.contrib.auth.models import User

from .models import Bartender, new_email_token

class BartenderTokenBackend:
	def authenticate(self, request, username=None, token=None):
		try:
			bartender = Bartender.objects.get(username=username, email_token=token)
			bartender.email_token = new_email_token()
			bartender.save()

			user, _ = User.objects.get_or_create(username=username)
			return user
		except Bartender.DoesNotExist:
			return None

	def get_user(self, user_id):
		try:
			return User.objects.get(pk=user_id)
		except User.DoesNotExist:
			return None

	def has_perm(self, user_obj, perm, obj=None):
		if perm != 'bartenders.change_bartender':
			return False

		print('has_perm', obj)
		if obj:
			return user_obj.username == obj.username

		return True
