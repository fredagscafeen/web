from urllib.parse import urljoin

from captcha.fields import ReCaptchaField
from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from bartab.models import BarTabUser
from bartenders.models import Bartender, BartenderApplication
from fredagscafeen.email import send_template_email


class BartenderApplicationForm(forms.ModelForm):
    captcha = ReCaptchaField()

    class Meta:
        model = BartenderApplication
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["tshirt_size"].widget.attrs.update({"class": "form-control"})
        for name in self.fields:
            self.fields[name].required = name != "info"

    def send_email(self, pk):
        d = self.cleaned_data

        url = urljoin(
            settings.SELF_URL,
            reverse("admin:bartenders_bartenderapplication_change", args=(pk,)),
        )

        extra_info = ""
        if d["info"]:
            extra_info = f"""
Ekstra information:
{d["info"]}
"""
        d["extra_info"] = extra_info

        return send_template_email(
            subject=f'Bartendertilmelding: {d["name"]}',
            body_template="""Dette er en automatisk email.

{name} har ansøgt om at blive bartender:
Navn: {name}
Brugernavn: {username}
Studienummer: {studentNumber}
Email: {email}
Telefonnummer: {phoneNumber}
{extra_info}
Ansøgningen kan blive accepteret eller afvist i {link}.

/snek""",
            text_format={"link": f"admin interfacet: {url}", **d},
            html_format={
                "link": mark_safe(f'<a href="{url}">admin interfacet</a>'),
                **d,
            },
            to=[settings.BEST_MAIL],
        )

    def send_confirmation_email(self, pk):
        d = self.cleaned_data

        extra_info = ""
        if d["info"]:
            extra_info = f"""
Ekstra information:
{d["info"]}
"""
        d["extra_info"] = extra_info

        return send_template_email(
            subject=f"Kvittering for bartendertilmelding til fredagscaféen",
            body_template="""Dette er en automatisk email.

Hej {name},

Tak for din ansøgning om at blive bartender i fredagscaféen!
Vi gennemgår din ansøgning på næste bestyrelsesmøde, så forvent lidt ventetid, før du hører fra os.

Kopi af din ansøgning:

Navn: {name}
Brugernavn: {username}
Studienummer: {studentNumber}
Email: {email}
Telefonnummer: {phoneNumber}
{extra_info}

/Bestyrelsen""",
            text_format={**d},
            html_format={
                **d,
            },
            to=[d["email"]],
        )


class BartenderInfoForm(forms.ModelForm):
    class Meta:
        model = Bartender
        fields = (
            "name",
            "username",
            "email",
            "studentNumber",
            "phoneNumber",
            "tshirt_size",
            "color",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["tshirt_size"].widget.attrs.update({"class": "form-control"})
        self.fields["username"].disabled = True
        # Add color options with visual preview
        COLOR_CHOICES = (
            ("red", ""),
            ("yellow", ""),
            ("green", ""),
            ("blue", ""),
            ("orange", ""),
        )
        self.fields["color"].widget = forms.RadioSelect(choices=COLOR_CHOICES)
        self.fields["color"].widget.attrs.update({"class": "color-selector"})

        # Add CSS styling for color visualization
        color_css = """
        <style>
        .color-selector { display: flex; gap: 10px; }
        .color-selector label { display: flex; align-items: center; margin: 0; }
        .color-selector input[type="radio"] {
            appearance: none;
            width: 30px;
            height: 30px;
            border: 2px solid #ccc;
            border-radius: 50%;
            cursor: pointer;
        }
        .color-selector input[value="red"] { background-color: red; }
        .color-selector input[value="yellow"] { background-color: yellow; }
        .color-selector input[value="green"] { background-color: green; }
        .color-selector input[value="blue"] { background-color: blue; }
        .color-selector input[value="orange"] { background-color: orange; }
        .color-selector input[type="radio"]:checked {
            border-color: #000;
            box-shadow: 0 0 5px rgba(0,0,0,0.5);
        }
        .color-selector label .form-check-label { display: none; }
        </style>
        """
        self.fields["color"].help_text = mark_safe(color_css)

    def save(self, *args, **kwargs):
        old_obj = type(self.instance).objects.get(id=self.instance.id)
        obj = super().save(*args, **kwargs)
        if old_obj.email != obj.email:
            # Update mailing lists
            for list_and_password in [Bartender.MAILMAN_ALL, Bartender.MAILMAN_BEST]:
                if old_obj.is_on_mailing_list(list_and_password):
                    old_obj.remove_from_mailing_list(list_and_password)
                    obj.add_to_mailing_list(list_and_password)

            # Update bartab user
            BarTabUser.objects.filter(email=old_obj.email).update(email=obj.email)

            # Update django user
            # There might be multiple users with that email
            for user in User.objects.filter(email=old_obj.email):
                if user.username.startswith("ZZZZZ_email_"):
                    user.delete()
                else:
                    user.email = obj.email
                    user.save()

        return obj


class BallotsUpdateForm(forms.Form):
    name = forms.CharField()
    urls = forms.CharField(widget=forms.Textarea)
