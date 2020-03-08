from django import forms

from .models import Printer


class PrintForm(forms.Form):
    printer = forms.ModelChoiceField(label="Printer", queryset=Printer.objects)
