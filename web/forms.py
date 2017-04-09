from urllib.parse import urljoin

from django.conf import settings
from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse
from django.forms import ModelForm
from django.utils.safestring import mark_safe
from captcha.fields import ReCaptchaField

from bartenders.models import BartenderApplication


class BartenderApplicationForm(ModelForm):
	captcha = ReCaptchaField()

	class Meta:
		model = BartenderApplication
		fields = '__all__'

	def send_email(self, pk):
		d = self.cleaned_data

		url = urljoin(settings.SELF_URL, reverse('admin:bartenders_bartenderapplication_change', args=(pk,)))

		subject = 'Bartender application: %s' % d['name']
		body = ('This is an automated email.\n\n'
		        '{name} has applied to become a bartender:\n'
		        '{name} ({username})\n'
		        '{studentNumber} - {email}\n'
		        '{phoneNumber}\n\n'
		        + ('Extra info:\n{info}\n\n' if d['info'] else '') +
		        'The application can be accepted or denied through {link}.\n\n'
		        '/snek').format(link=mark_safe('<a href="{url}">the admin interface</a>'.format(url=url)), **d)

		email = EmailMessage(subject=subject, body=body, from_email='best@fredagscafeen.dk',
		                     to=['best@fredagscafeen.dk'], cc=['best@fredagscafeen.dk'])
		return email.send()
