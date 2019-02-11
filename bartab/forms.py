from django import forms

from .models import BarTabSnapshot, Printer


class ConsumptionForm(forms.Form):
	start_snapshot = forms.ModelChoiceField(label='First to include', queryset=BarTabSnapshot.objects)
	end_snapshot = forms.ModelChoiceField(label='Last to include', queryset=BarTabSnapshot.objects)


class PrintForm(forms.Form):
	printer = forms.ModelChoiceField(label='Printer', queryset=Printer.objects)
