from django.contrib import admin
from django.contrib.admin.models import LogEntry
from logentry_admin.admin import LogEntryAdmin
from django.urls import path
from admin_views.admin import AdminViews
from django.conf import settings
from django.template.response import TemplateResponse


class LogEntryAdminWithSecrets(LogEntryAdmin, AdminViews):
	admin_views = (
		('Secrets', 'secrets_view'),
	)

	def secrets_view(self, request):
		secrets = [(title, getattr(settings, key, None)) for key, title in settings.SECRET_ADMIN_KEYS]

		context = dict(
			# Include common variables for rendering the admin template.
			self.admin_site.each_context(request),
			# Anything else you want in the context...
			secrets=secrets,
		)
		return TemplateResponse(request, "secrets_admin.html", context)


admin.site.unregister(LogEntry)
admin.site.register(LogEntry, LogEntryAdminWithSecrets)
