from django import forms
from unfold.contrib.forms.widgets import UnfoldAdminSelectWidget

from .models import Printer


class PrintForm(forms.Form):
    printer = forms.ModelChoiceField(
        label="Printer",
        queryset=Printer.objects,
        widget=UnfoldAdminSelectWidget,
    )
