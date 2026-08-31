from django.contrib import admin, messages
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, reverse
from django.template.response import TemplateResponse
from django.urls import path
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from unfold.admin import TabularInline

from fredagscafeen.admin import CustomModelAdmin
from fredagscafeen.admin_view import custom_admin_view

from .forms import (
    ExpenseItemFormSet,
    OutOfPocketExpenseAdminForm,
    OutOfPocketExpenseForm,
)
from .models import ExpenseAttachment, OutOfPocketExpense, OutOfPocketExpenseItem
from .services import build_expense_attachment_download_url, upload_expense_attachment


class ExpenseAttachmentInline(TabularInline):
    model = ExpenseAttachment
    extra = 0
    fields = ("download_link",)
    readonly_fields = ("download_link",)

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def download_link(self, obj):
        if not obj.pk:
            return "-"
        filename = obj.s3_object_key.rsplit("/", 1)[-1]
        url = reverse("admin:accountant_expenseattachment_download", args=[obj.pk])
        return format_html(
            '<a href="{}" class="text-primary-600 dark:text-primary-400 font-medium hover:underline">{}</a>',
            url,
            filename,
        )

    download_link.short_description = _("Attachment")


class OutOfPocketExpenseItemInline(TabularInline):
    model = OutOfPocketExpenseItem
    extra = 0
    fields = ("description", "amount", "notes")
    inlines = [ExpenseAttachmentInline]

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(OutOfPocketExpense)
class OutOfPocketExpenseAdmin(CustomModelAdmin):
    form = OutOfPocketExpenseAdminForm
    autocomplete_fields = ("bartender",)
    list_display = (
        "bartender",
        "bank_registration_number",
        "bank_account_number",
        "total_amount_display",
        "completed",
        "created_at",
    )
    list_filter = ("completed",)
    inlines = [OutOfPocketExpenseItemInline]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.has_perm("accountant.complete_expenses")

    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        editable = set()
        if request.user.has_perm("accountant.complete_expenses"):
            editable.add("completed")
        return [
            field.name
            for field in self.model._meta.fields
            if field.name != "id" and field.name not in editable
        ]

    def total_amount_display(self, obj):
        return f"{obj.total_amount} DKK"

    total_amount_display.short_description = _("Total amount")

    def get_urls(self):
        return [
            path(
                "download-attachment/<int:attachment_id>/",
                self.admin_site.admin_view(self.download_attachment),
                name="accountant_expenseattachment_download",
            ),
        ] + super().get_urls()

    def download_attachment(self, request, attachment_id):
        attachment = get_object_or_404(ExpenseAttachment, pk=attachment_id)
        try:
            download_url = build_expense_attachment_download_url(attachment)
        except ImproperlyConfigured as error:
            self.message_user(request, str(error), messages.ERROR)
            return HttpResponseRedirect(
                reverse(
                    "admin:accountant_outofpocketexpense_change",
                    args=[attachment.expense_item.expense_id],
                )
            )

        return HttpResponseRedirect(download_url)


@custom_admin_view("accountant", "add out of pocket expense")
def add_out_of_pocket_expense(admin, request):
    if request.method == "POST":
        expense_form = OutOfPocketExpenseForm(request.POST)
        item_formset = ExpenseItemFormSet(request.POST, request.FILES, prefix="items")

        if expense_form.is_valid() and item_formset.is_valid():
            with transaction.atomic():
                expense = expense_form.save()

                item_formset.instance = expense
                item_formset.save()

                for i, form in enumerate(item_formset.forms):
                    if not form.instance.pk:
                        continue

                    item = form.instance
                    for uploaded_file in request.FILES.getlist(
                        f"items-{i}-attachments"
                    ):
                        object_key = upload_expense_attachment(uploaded_file, item)
                        ExpenseAttachment.objects.create(
                            expense_item=item,
                            s3_object_key=object_key,
                        )

            admin.message_user(request, _("Expense claim submitted."))
            expense_form = OutOfPocketExpenseForm()
            item_formset = ExpenseItemFormSet(prefix="items")
    else:
        expense_form = OutOfPocketExpenseForm()
        item_formset = ExpenseItemFormSet(prefix="items")

    context = dict(
        admin.admin_site.each_context(request),
        title=_("Add out of pocket expense"),
        expense_form=expense_form,
        item_formset=item_formset,
    )
    return TemplateResponse(request, "admin/expense_form.html", context)
