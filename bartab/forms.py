from django import forms
from django.utils.translation import gettext_lazy as _
from unfold.widgets import UnfoldAdminSelectWidget

from .models import BarTabSnapshot


class ConsumptionForm(forms.Form):
    start_snapshot = forms.ModelChoiceField(
        label=_("First to include"),
        queryset=BarTabSnapshot.objects,
        widget=UnfoldAdminSelectWidget,
    )
    end_snapshot = forms.ModelChoiceField(
        label=_("Last to include"),
        queryset=BarTabSnapshot.objects,
        widget=UnfoldAdminSelectWidget,
    )
