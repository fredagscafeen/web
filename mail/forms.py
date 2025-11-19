from django import forms
from django.utils.translation import gettext_lazy as _

from fredagscafeen.email import send_template_email

from .models import OutgoingEmail


class OutgoingEmailAdminForm(forms.ModelForm):
    class Meta:
        model = OutgoingEmail
        fields = "__all__"
        verbose_name = _("Send email")
        verbose_name_plural = _("Send emails")
