from crispy_forms.helper import FormHelper
from django import forms
from django.forms import inlineformset_factory
from unfold.widgets import UnfoldAdminTextInputWidget

from bartenders.models import Bartender

from .models import OutOfPocketExpense, OutOfPocketExpenseItem


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

    def __init__(self, attrs=None):
        default_attrs = {"class": "file-input"}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_file_clean(d, initial) for d in data]
        return single_file_clean(data, initial)


class OutOfPocketExpenseAdminForm(forms.ModelForm):
    class Meta:
        model = OutOfPocketExpense
        fields = "__all__"
        widgets = {
            "bank_registration_number": UnfoldAdminTextInputWidget(
                attrs={
                    "placeholder": "1234",
                    "style": "width: 100px;",
                    "class": "font-mono",
                }
            ),
            "bank_account_number": UnfoldAdminTextInputWidget(
                attrs={
                    "placeholder": "1234567890",
                    "style": "width: 200px;",
                    "class": "font-mono",
                }
            ),
        }


class OutOfPocketExpenseForm(forms.ModelForm):
    class Meta:
        model = OutOfPocketExpense
        fields = ["bartender", "bank_registration_number", "bank_account_number"]
        widgets = {
            "bank_registration_number": forms.TextInput(attrs={"placeholder": "1234"}),
            "bank_account_number": forms.TextInput(attrs={"placeholder": "1234567890"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["bartender"].queryset = Bartender.objects.filter(
            isActiveBartender=True
        )
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.disable_csrf = True


class OutOfPocketExpenseItemForm(forms.ModelForm):
    attachments = MultipleFileField(required=False, label="Receipts")

    class Meta:
        model = OutOfPocketExpenseItem
        fields = ["description", "amount", "notes"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.disable_csrf = True


ExpenseItemFormSet = inlineformset_factory(
    OutOfPocketExpense,
    OutOfPocketExpenseItem,
    form=OutOfPocketExpenseItemForm,
    extra=1,
    can_delete=False,
)
