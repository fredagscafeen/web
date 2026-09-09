from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Div, Field, Layout
from django import forms
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
from django.forms import inlineformset_factory
from unfold.widgets import UnfoldAdminTextInputWidget

ALLOWED_ATTACHMENT_EXTENSIONS = ["jpg", "jpeg", "png", "pdf"]

from .models import OutOfPocketExpense, OutOfPocketExpenseItem

User = get_user_model()


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

    def __init__(self, attrs=None):
        default_attrs = {
            "class": "file-input",
            "accept": ",".join(f".{ext}" for ext in ALLOWED_ATTACHMENT_EXTENSIONS),
        }
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

    def has_changed(self, initial, data):
        # With allow_multiple_selected, an untouched widget reports data=[]
        # rather than None - FileField.has_changed() only treats None as
        # "unchanged", so [] was wrongly marking the blank extra formset row
        # as changed and dragging it into full required-field validation.
        if self.disabled:
            return False
        return bool(data)


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

    def __init__(
        self, *args, bank_fields_editable=False, completed_editable=False, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.fields["user"].disabled = True
        if not bank_fields_editable:
            self.fields["bank_registration_number"].disabled = True
            self.fields["bank_account_number"].disabled = True
        if not completed_editable:
            self.fields["completed"].disabled = True
        self.fields["completed"].widget.attrs.update(
            {"class": "h-5 w-5 accent-primary-600"}
        )
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.helper.layout = Layout(
            "user",
            "bank_registration_number",
            "bank_account_number",
            Div(
                Field("completed"),
                css_class=(
                    "mt-4 p-4 rounded-default border-2 border-primary-500 "
                    "bg-primary-50 dark:bg-primary-950/40 text-base font-semibold"
                ),
            ),
        )


class OutOfPocketExpenseForm(forms.ModelForm):
    class Meta:
        model = OutOfPocketExpense
        fields = ["user", "bank_registration_number", "bank_account_number"]
        widgets = {
            "bank_registration_number": forms.TextInput(attrs={"placeholder": "1234"}),
            "bank_account_number": forms.TextInput(attrs={"placeholder": "1234567890"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["user"].queryset = User.objects.filter(is_staff=True)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.disable_csrf = True


ATTACHMENT_LINKS_HTML = """
<label class="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">Receipts</label>
{% if form.instance.pk %}
<div class="expense-item-attachments flex flex-col gap-1 mb-2 divide-y divide-gray-200 dark:divide-gray-700">
    {% for attachment in form.instance.attachments.all %}
        <div class="pb-2">
            <a href="{% url 'admin:accountant_expenseattachment_download' attachment.pk %}"
               class="text-primary-600 dark:text-primary-400 font-medium hover:underline">
                {{ attachment.filename }}
            </a>
            <span class="text-gray-500 dark:text-gray-400 text-sm ml-2">
                {{ attachment.created_at }}
            </span>
        </div>
    {% endfor %}
</div>
{% endif %}
"""


class OutOfPocketExpenseItemForm(forms.ModelForm):
    attachments = MultipleFileField(
        required=False,
        label="",
        validators=[
            FileExtensionValidator(allowed_extensions=ALLOWED_ATTACHMENT_EXTENSIONS)
        ],
    )

    class Meta:
        model = OutOfPocketExpenseItem
        fields = ["description", "date", "amount", "notes"]
        widgets = {
            # type="date" requires an ISO value; the browser then displays it
            # per the user's own locale (already DD-MM-YYYY for Danish users)
            "date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }

    def __init__(self, *args, editable=True, **kwargs):
        super().__init__(*args, **kwargs)
        if not editable:
            del self.fields["attachments"]
            for name in ("description", "date", "amount", "notes"):
                self.fields[name].disabled = True

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.disable_csrf = True

        layout_fields = [
            "id",
            "description",
            "date",
            "amount",
            "notes",
            HTML(ATTACHMENT_LINKS_HTML),
        ]
        if editable:
            # DELETE is driven by the styled "Remove item" button in JS, not shown directly
            layout_fields += ["attachments", Field("DELETE", wrapper_class="hidden")]
        self.helper.layout = Layout(*layout_fields)


def build_expense_item_formset(editable):
    return inlineformset_factory(
        OutOfPocketExpense,
        OutOfPocketExpenseItem,
        form=OutOfPocketExpenseItemForm,
        extra=1 if editable else 0,
        can_delete=editable,
    )


ExpenseItemFormSet = build_expense_item_formset(editable=True)
