from django.db import models
from django.utils.translation import gettext_lazy as _

from bartenders.models import Bartender
from web.models import TimeStampedModel


class OutOfPocketExpense(TimeStampedModel):
    class Meta:
        verbose_name = _("Out of Pocket Expense")
        verbose_name_plural = _("Out of Pocket Expenses")
        permissions = [
            ("complete_expenses", "Can mark out of pocket expenses as completed"),
        ]

    bartender = models.ForeignKey(
        Bartender,
        on_delete=models.CASCADE,
        related_name="out_of_pocket_expenses",
    )

    bank_registration_number = models.CharField(
        max_length=4,
        verbose_name=_("Bank Registration Number"),
        help_text=_(
            "The registration number of the bank account. i.e. the first four digits of the account number."
        ),
    )
    bank_account_number = models.CharField(
        max_length=10,
        verbose_name=_("Bank Account Number"),
        help_text=_("The account number without the registration number."),
    )
    completed = models.BooleanField(
        default=False,
        verbose_name=_("Completed"),
        help_text=_("Whether this expense has been paid out."),
    )

    def __str__(self):
        return f"{self.bartender.name} - {self.created_at.strftime('%Y-%m-%d')} - {self.total_amount} DKK"

    @property
    def total_amount(self):
        return sum(item.amount for item in self.items.all())


class OutOfPocketExpenseItem(TimeStampedModel):
    class Meta:
        verbose_name = _("Out of Pocket Expense Item")
        verbose_name_plural = _("Out of Pocket Expense Items")

    expense = models.ForeignKey(
        OutOfPocketExpense,
        on_delete=models.CASCADE,
        related_name="items",
    )
    description = models.CharField(
        max_length=255,
        verbose_name=_("Description"),
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_("Notes"),
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Amount"),
        help_text=_("The amount in DKK."),
    )


class ExpenseAttachment(TimeStampedModel):
    class Meta:
        verbose_name = _("Expense Attachment")
        verbose_name_plural = _("Expense Attachments")

    expense_item = models.ForeignKey(
        OutOfPocketExpenseItem,
        on_delete=models.CASCADE,
        related_name="attachments",
    )
    s3_object_key = models.CharField(max_length=1024)
