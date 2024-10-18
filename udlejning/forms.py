from urllib.parse import urljoin

from bootstrap_datepicker_plus.widgets import DateTimePickerInput
from captcha.fields import ReCaptchaField
from captcha.widgets import ReCaptchaV2Invisible
from django import forms
from django.conf import settings
from django.urls import reverse
from django.utils.safestring import mark_safe

from fredagscafeen.email import send_template_email

from .models import UdlejningApplication


class UdlejningApplicationForm(forms.ModelForm):
    captcha = ReCaptchaField(widget=ReCaptchaV2Invisible)

    class Meta:
        model = UdlejningApplication
        fields = "__all__"
        widgets = {
            "dateFrom": DateTimePickerInput(),
            "dateTo": DateTimePickerInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["captcha"].help_text = "Hjemmesiden er sikret med reCAPTCHAv2"
        self.fields["paymentType"].widget.attrs.update({"class": "form-control"})
        for name in self.fields:
            self.fields[name].required = name not in ["EANnumber", "comments"]

    def clean(self):
        super().clean()

        d_from = self.cleaned_data.get("dateFrom")
        d_to = self.cleaned_data.get("dateTo")

        if d_to and d_from and d_from > d_to:
            self.add_error(
                "dateTo", f'"Til" tidspunkt skal komme efter "fra" tidspunkt'
            )

    def send_email(self, pk):
        d = self.cleaned_data

        url = urljoin(
            settings.SELF_URL,
            reverse("admin:udlejning_udlejningapplication_change", args=(pk,)),
        )

        return send_template_email(
            subject=f'Ny anmodning om reservation af fadølsanlæg af {d["whoReserved"]}',
            body_template="""Dette er en automatisk email.

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
/snek""",
            text_format={"link": f"admin interfacet: {url}", **d},
            html_format={
                "link": mark_safe(f'<a href="{url}">admin interfacet</a>'),
                **d,
            },
            to=["best@fredagscafeen.dk"],
        )
