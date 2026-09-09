import zipfile
from io import BytesIO
from tempfile import TemporaryDirectory

from django.conf import settings
from django.contrib import admin, messages
from django.contrib.admin.utils import unquote
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.db import transaction
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, reverse
from django.template.response import TemplateResponse
from django.urls import path
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from fredagscafeen.admin import CustomModelAdmin
from fredagscafeen.admin_view import custom_admin_view
from printer.latex import LatexError, generate_pdf

from .forms import (
    ExpenseItemFormSet,
    OutOfPocketExpenseAdminForm,
    OutOfPocketExpenseForm,
    build_expense_item_formset,
)
from .models import ExpenseAttachment, OutOfPocketExpense
from .services import (
    build_expense_attachment_download_url,
    get_expense_attachment_bytes,
    upload_expense_attachment,
)


class ExpenseVoucherContext:
    file_path = "admin/expense_voucher.tex"

    def __init__(self, expense):
        self.expense = expense
        self.file_name = f"expense_voucher_{expense.pk}"

    def get_context(self):
        items = [
            {
                "date": item.date,
                "description": item.description,
                "amount": item.amount,
                "notes": item.notes,
                "attachments": [
                    attachment.filename for attachment in item.attachments.all()
                ],
            }
            for item in self.expense.items.all()
        ]
        return {
            "logo_path": settings.STATIC_ROOT + "images/logo.png",
            "user_name": f"{self.expense.user.first_name} {self.expense.user.last_name}",
            "bank_registration_number": self.expense.bank_registration_number,
            "bank_account_number": self.expense.bank_account_number,
            "items": items,
            "total": self.expense.total_amount,
        }


def _is_editable_by_creator(request, obj):
    """Strict, obj-required check: is this specific expense editable by its creator right now?

    Owning the expense wins even if the user also holds complete_expenses -
    filing your own claim shouldn't lock you out of editing it.
    """
    if obj is None:
        return False
    if obj.completed:
        return False
    return obj.user_id == request.user.id


def _build_expense_bundle_zip(expense):
    """Build the udgiftsbilag ZIP (voucher PDF + attachments) for a single expense.

    May raise LatexError or ImproperlyConfigured - callers handle those.
    """
    context = ExpenseVoucherContext(expense)
    with TemporaryDirectory() as work_dir:
        pdf_path = generate_pdf(work_dir, context)
        with open(pdf_path, "rb") as f:
            pdf_data = f.read()

    attachments = [
        attachment
        for item in expense.items.all()
        for attachment in item.attachments.all()
    ]
    attachment_files = [
        (attachment, get_expense_attachment_bytes(attachment))
        for attachment in attachments
    ]

    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(f"udgiftsbilag-{expense.pk}.pdf", pdf_data)

        used_names = set()
        for attachment, data in attachment_files:
            filename = attachment.filename
            name = filename
            suffix = 1
            while name in used_names:
                stem, _sep, ext = filename.rpartition(".")
                name = f"{stem or filename}-{suffix}{('.' + ext) if ext else ''}"
                suffix += 1
            used_names.add(name)
            archive.writestr(f"bilag/{name}", data)

    return buffer.getvalue()


@admin.register(OutOfPocketExpense)
class OutOfPocketExpenseAdmin(CustomModelAdmin):
    autocomplete_fields = ("user",)
    list_display = (
        "completed",
        "user",
        "total_amount_display",
        "bank_registration_number",
        "bank_account_number",
        "created_at",
        "voucher_link",
    )
    list_filter = ("completed",)
    actions = ["mark_as_completed", "download_selected_bundles"]

    def has_view_permission(self, request, obj=None):
        return True

    def has_add_permission(self, request):
        # Creation happens through the custom add view; this only makes the
        # standard "+ Add" changelist button appear, see add_view below.
        return True

    def add_view(self, request, form_url="", extra_context=None):
        return HttpResponseRedirect(
            reverse("admin:accountant_add_out_of_pocket_expense_changelist")
        )

    def has_change_permission(self, request, obj=None):
        if request.user.has_perm("accountant.complete_expenses"):
            return True
        if obj is None:
            return True
        return not obj.completed and obj.user_id == request.user.id

    def has_delete_permission(self, request, obj=None):
        return False

    def has_mark_as_completed_permission(self, request):
        return request.user.has_perm("accountant.complete_expenses")

    def change_view(self, request, object_id, form_url="", extra_context=None):
        obj = self.get_object(request, unquote(object_id))
        if obj is None:
            raise Http404

        if request.method == "POST" and not self.has_change_permission(request, obj):
            raise PermissionDenied

        items_editable = _is_editable_by_creator(request, obj)
        completed_editable = request.user.has_perm("accountant.complete_expenses")
        show_submit = self.has_change_permission(request, obj)
        item_formset_class = build_expense_item_formset(items_editable)

        if request.method == "POST":
            expense_form = OutOfPocketExpenseAdminForm(
                request.POST,
                instance=obj,
                bank_fields_editable=items_editable,
                completed_editable=completed_editable,
            )
            if items_editable:
                item_formset = item_formset_class(
                    request.POST,
                    request.FILES,
                    instance=obj,
                    prefix="items",
                    form_kwargs={"editable": items_editable},
                )
                item_formset_valid = item_formset.is_valid()
            else:
                item_formset = item_formset_class(
                    instance=obj,
                    prefix="items",
                    form_kwargs={"editable": items_editable},
                )
                item_formset_valid = True

            if expense_form.is_valid() and item_formset_valid:
                with transaction.atomic():
                    expense_form.save()

                    if items_editable:
                        item_formset.save()

                        for i, item_form in enumerate(item_formset.forms):
                            if (
                                not item_form.instance.pk
                                or item_form in item_formset.deleted_forms
                            ):
                                continue

                            item = item_form.instance
                            for uploaded_file in request.FILES.getlist(
                                f"items-{i}-attachments"
                            ):
                                object_key = upload_expense_attachment(
                                    uploaded_file, item
                                )
                                ExpenseAttachment.objects.create(
                                    expense_item=item,
                                    s3_object_key=object_key,
                                )

                self.message_user(request, _("Expense saved."))
                return HttpResponseRedirect(
                    reverse("admin:accountant_outofpocketexpense_change", args=[obj.pk])
                )
        else:
            expense_form = OutOfPocketExpenseAdminForm(
                instance=obj,
                bank_fields_editable=items_editable,
                completed_editable=completed_editable,
            )
            item_formset = item_formset_class(
                instance=obj,
                prefix="items",
                form_kwargs={"editable": items_editable},
            )

        context = dict(
            self.admin_site.each_context(request),
            title=str(obj),
            expense_form=expense_form,
            item_formset=item_formset,
            items_editable=items_editable,
            show_submit=show_submit,
        )
        return TemplateResponse(request, "admin/expense_form.html", context)

    @admin.action(
        description=_("Mark selected expenses as completed"),
        permissions=["mark_as_completed"],
    )
    def mark_as_completed(self, request, queryset):
        updated = queryset.filter(completed=False).update(completed=True)
        self.message_user(
            request,
            _("Marked %(count)d expense(s) as completed.") % {"count": updated},
        )

    @admin.action(description=_("Download selected expenses as ZIP bundles"))
    def download_selected_bundles(self, request, queryset):
        skipped = []
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            for expense in queryset.prefetch_related("items__attachments"):
                try:
                    data = _build_expense_bundle_zip(expense)
                except (LatexError, ImproperlyConfigured) as error:
                    skipped.append(f"{expense} ({error})")
                    continue
                archive.writestr(f"expense-{expense.pk}.zip", data)

        if skipped:
            self.message_user(
                request,
                _("Skipped %(count)d expense(s): %(details)s")
                % {"count": len(skipped), "details": "; ".join(skipped)},
                messages.WARNING,
            )

        response = HttpResponse(buffer.getvalue(), content_type="application/zip")
        response["Content-Disposition"] = 'attachment; filename="udgiftsbilag.zip"'
        return response

    def total_amount_display(self, obj):
        return f"{obj.total_amount} DKK"

    total_amount_display.short_description = _("Total amount")

    def voucher_link(self, obj):
        if not obj.pk:
            return "-"
        url = reverse("admin:accountant_outofpocketexpense_bundle", args=[obj.pk])
        return format_html(
            '<a href="{}" class="text-primary-600 dark:text-primary-400 font-medium hover:underline">{}</a>',
            url,
            _("Download ZIP"),
        )

    voucher_link.short_description = _("Udgiftsbilag")

    def get_urls(self):
        return [
            path(
                "download-attachment/<int:attachment_id>/",
                self.admin_site.admin_view(self.download_attachment),
                name="accountant_expenseattachment_download",
            ),
            path(
                "download-bundle/<int:object_id>/",
                self.admin_site.admin_view(self.download_bundle),
                name="accountant_outofpocketexpense_bundle",
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

    def download_bundle(self, request, object_id):
        expense = get_object_or_404(
            OutOfPocketExpense.objects.prefetch_related("items__attachments"),
            pk=object_id,
        )
        try:
            data = _build_expense_bundle_zip(expense)
        except LatexError as error:
            self.message_user(request, error.message, messages.ERROR)
            return HttpResponseRedirect(
                reverse("admin:accountant_outofpocketexpense_change", args=[object_id])
            )
        except ImproperlyConfigured as error:
            self.message_user(request, str(error), messages.ERROR)
            return HttpResponseRedirect(
                reverse("admin:accountant_outofpocketexpense_change", args=[object_id])
            )

        response = HttpResponse(data, content_type="application/zip")
        response["Content-Disposition"] = (
            f'attachment; filename="udgiftsbilag-{expense.pk}.zip"'
        )
        return response


@custom_admin_view("accountant", "add out of pocket expense", show_in_sidebar=False)
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
            expense_form = OutOfPocketExpenseForm(initial={"user": request.user.pk})
            item_formset = ExpenseItemFormSet(prefix="items")
    else:
        expense_form = OutOfPocketExpenseForm(initial={"user": request.user.pk})
        item_formset = ExpenseItemFormSet(prefix="items")

    context = dict(
        admin.admin_site.each_context(request),
        title=_("Add out of pocket expense"),
        expense_form=expense_form,
        item_formset=item_formset,
        items_editable=True,
        show_submit=True,
    )
    return TemplateResponse(request, "admin/expense_form.html", context)
