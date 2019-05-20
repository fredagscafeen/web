from urllib.parse import urljoin

from captcha.fields import ReCaptchaField
from django.conf import settings
from django.urls import reverse
from django import forms
from django.utils import timezone
from django.utils.safestring import mark_safe
from bootstrap_datepicker_plus import DateTimePickerInput

from email_auth.auth import EmailTokenBackend
from email_auth.models import EmailToken
from bartenders.models import Bartender, BartenderShift, BartenderApplication, BoardMemberPeriod
from udlejning.models import UdlejningApplication
from fredagscafeen.email import send_template_email


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


class LoginForm(forms.Form):
	email = forms.EmailField()
	captcha = ReCaptchaField()

	def clean_email(self):
		email = self.cleaned_data['email']
		if not EmailTokenBackend.is_user(email):
			raise forms.ValidationError('Ukendt email')

		return email

	def send_email(self, next):
		email_address = self.cleaned_data['email']

		email_token, _ = EmailToken.objects.get_or_create(email=email_address)

		url = urljoin(settings.SELF_URL, reverse('email_login', args=(email_address, email_token.token)))
		if next:
			url += f'?next={next}'

		return send_template_email(
			subject='fredagscafeen.dk login',
			body_template='''{link} for at logge ind.

/snek''',
			text_format={'link': f'Gå ind på {url}'},
			html_format={'link': mark_safe(f'<a href="{url}">Klik her</a>')},
			to=[email_address]
		)


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


class UdlejningApplicationForm(forms.ModelForm):
	captcha = ReCaptchaField()

	class Meta:
		model = UdlejningApplication
		fields = '__all__'
		widgets = {
			'dateFrom': DateTimePickerInput(format='%Y-%m-%d %H:%M'),
			'dateTo': DateTimePickerInput(format='%Y-%m-%d %H:%M')
		}

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		for name in self.fields:
			self.fields[name].required = name not in ['EANnumber', 'comments']

	def send_email(self, pk):
		d = self.cleaned_data

		url = urljoin(settings.SELF_URL, reverse('admin:udlejning_udlejningapplication_change', args=(pk,)))

		return send_template_email(
			subject=f'Ny anmodning om reservation af fadølsanlæg af {d["whoReserved"]}',
			body_template='''Dette er en automatisk email.

{whoReserved} har ansøgt om at låne et fadølsanlæg:
Dato: {dateFrom} til {dateTo}
Kontakt email: {contactEmail}
Kontakt telefonnummer: {contactPhone}
Betaler: {whoPays}
Betalingsform: {paymentType}
EAN-nummer: {EANnumber}
Lokation: {where}
Forventet forbrug: {expectedConsummation}
Kommentarer:
{comments}

Ansøgningen kan blive accepteret eller afvist i {link} ,
men husk at kontakte personen efter dette.
/snek''',
			text_format={'link': f'admin interfacet: {url}', **d},
			html_format={'link': mark_safe(f'<a href="{url}">admin interfacet</a>'), **d},
			to=['best@fredagscafeen.dk']
		)


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

		self.fields['bartender_shift1'].queryset = BartenderShift.with_bartender(bartender1).filter(end_datetime__gte=timezone.now()).reverse()
		self.fields['bartender_shift2'].queryset = BartenderShift.with_bartender(bartender2).filter(end_datetime__gte=timezone.now()).reverse()

		if not swap:
			del self.fields['bartender_shift2']
