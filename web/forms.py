from urllib.parse import urljoin

from captcha.fields import ReCaptchaField
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.forms import ModelForm
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

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
		        '/snek').format(link='{link}', **d)

		body_text = render_to_string('email.txt', {'content': body.format(link='the admin interface: %s' % url)})
		body_html = render_to_string('email.html', {'content': body.format(link=mark_safe('<a href="{url}">the admin interface</a>'.format(url=url)))})

		email = EmailMultiAlternatives(subject=subject, body=body_text, from_email='best@fredagscafeen.dk',
		                               to=['best@fredagscafeen.dk'], cc=['best@fredagscafeen.dk'])
		email.attach_alternative(body_html, 'text/html')
		return email.send()
