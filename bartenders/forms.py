from urllib.parse import urljoin
from django import forms
from django.conf import settings
from django.urls import reverse
from django.utils.safestring import mark_safe
from captcha.fields import ReCaptchaField
from fredagscafeen.email import send_template_email
from .models import Bartender, BartenderApplication


class BartenderApplicationForm(forms.ModelForm):
	captcha = ReCaptchaField()

	class Meta:
		model = BartenderApplication
		fields = '__all__'

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		for name in self.fields:
			self.fields[name].required = name != 'info'


	def send_email(self, pk):
		d = self.cleaned_data

		url = urljoin(settings.SELF_URL, reverse('admin:bartenders_bartenderapplication_change', args=(pk,)))

		extra_info = ''
		if d['info']:
			extra_info = f'''
Ekstra information:
{d["info"]}
'''
		d['extra_info'] = extra_info

		return send_template_email(
			subject=f'Bartendertilmelding: {d["name"]}',
			body_template='''Dette er en automatisk email.

{name} har ansøgt om at blive bartender:
Navn: {name}
Brugernavn: {username}
Studienummer: {studentNumber}
Email: {email}
Telefonnummer: {phoneNumber}
{extra_info}
Ansøgningen kan blive accepteret eller afvist i {link}.

/snek''',
			text_format={'link': f'admin interfacet: {url}', **d},
			html_format={'link': mark_safe(f'<a href="{url}">admin interfacet</a>'), **d},
			to=['best@fredagscafeen.dk']
		)


class BartenderInfoForm(forms.ModelForm):
	class Meta:
		model = Bartender
		fields = ('name', 'username', 'email', 'studentNumber', 'phoneNumber', 'tshirt_size', 'prefer_only_early_shifts')

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.fields['username'].disabled = True

		# email isn't currently editable as we need to handle
		# removing the old and possibly adding the new to the mailing list
		# another problem is also handling of ZZZZZ_email_ users
		self.fields['email'].disabled = True
