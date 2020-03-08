from django import forms

from .models import BarTabSnapshot


class ConsumptionForm(forms.Form):
    start_snapshot = forms.ModelChoiceField(
        label="First to include", queryset=BarTabSnapshot.objects
    )
    end_snapshot = forms.ModelChoiceField(
        label="Last to include", queryset=BarTabSnapshot.objects
    )
