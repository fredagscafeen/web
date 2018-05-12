from urllib.parse import urljoin

from captcha.fields import ReCaptchaField
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.urls import reverse
from django import forms
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from bartenders.models import Bartender, BartenderShift, BartenderApplication


class BartenderApplicationForm(forms.ModelForm):
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


class SwapForm1(forms.Form):
	bartender1 = forms.ModelChoiceField(label='Bartender 1', queryset=Bartender.objects)
	bartender2 = forms.ModelChoiceField(label='Bartender 2', queryset=Bartender.objects)
	swap = forms.BooleanField(help_text='(or replace 1 with 2)', initial=True, required=False)


class SwapForm2(SwapForm1):
	bartender_shift1 = forms.ModelChoiceField(label='Shift 1', queryset=BartenderShift.objects.none())
	bartender_shift2 = forms.ModelChoiceField(label='Shift 2', queryset=BartenderShift.objects.none())

	def __init__(self, *args, swap, bartender1, bartender2, **kwargs):
		super().__init__(*args, **kwargs)

		self.fields['bartender1'].initial = bartender1
		self.fields['bartender2'].initial = bartender2
		self.fields['swap'].initial = swap

		self.fields['bartender_shift1'].queryset = BartenderShift.with_bartender(bartender1.username)
		self.fields['bartender_shift2'].queryset = BartenderShift.with_bartender(bartender2.username)

		if not swap:
			del self.fields['bartender_shift2']
