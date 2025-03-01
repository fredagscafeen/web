from urllib.parse import urljoin

from captcha.fields import ReCaptchaField
from captcha.widgets import ReCaptchaV2Invisible
from django import forms
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from bartenders.models import Bartender, BartenderShift
from email_auth.auth import EmailTokenBackend
from email_auth.models import EmailToken
from fredagscafeen.email import send_template_email


class LoginForm(forms.Form):
    email = forms.EmailField()
    captcha = ReCaptchaField()

    def clean_email(self):
        email = self.cleaned_data["email"]
        if not EmailTokenBackend.is_user(email):
            raise forms.ValidationError("Ukendt email")

        return email

    def send_email(self, next):
        email_address = self.cleaned_data["email"]

        email_token, _ = EmailToken.objects.get_or_create(email=email_address)

        url = urljoin(
            settings.SELF_URL,
            reverse("email_login", args=(email_address, email_token.token)),
        )
        if next:
            url += f"?next={next}"

        return send_template_email(
            subject="fredagscafeen.dk login",
            body_template="""{link} for at logge ind.

/snek""",
            text_format={"link": f"Gå ind på {url}"},
            html_format={"link": mark_safe(f'<a href="{url}">Klik her</a>')},
            to=[email_address],
        )


class SwapForm1(forms.Form):
    bartender1 = forms.ModelChoiceField(label="Bartender 1", queryset=Bartender.objects)
    bartender2 = forms.ModelChoiceField(label="Bartender 2", queryset=Bartender.objects)
    swap = forms.BooleanField(
        help_text="(or replace 1 with 2)", initial=True, required=False
    )


class SwapForm2(SwapForm1):
    bartender_shift1 = forms.ModelChoiceField(
        label="Shift 1", queryset=BartenderShift.objects.none()
    )
    bartender_shift2 = forms.ModelChoiceField(
        label="Shift 2", queryset=BartenderShift.objects.none()
    )

    def __init__(self, *args, swap, bartender1, bartender2, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["bartender1"].initial = bartender1
        self.fields["bartender2"].initial = bartender2
        self.fields["swap"].initial = swap

        self.fields["bartender_shift1"].queryset = (
            BartenderShift.with_bartender(bartender1)
            .filter(end_datetime__gte=timezone.now())
            .reverse()
        )
        self.fields["bartender_shift2"].queryset = (
            BartenderShift.with_bartender(bartender2)
            .filter(end_datetime__gte=timezone.now())
            .reverse()
        )

        if not swap:
            del self.fields["bartender_shift2"]
