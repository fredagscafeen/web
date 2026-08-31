from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from bartenders.models import Bartender

from .models import ExpenseAttachment, OutOfPocketExpense, OutOfPocketExpenseItem
from .services import build_expense_attachment_download_url, upload_expense_attachment

User = get_user_model()

ADD_EXPENSE_URL_NAME = "admin:accountant_add_out_of_pocket_expense_changelist"


class UploadExpenseAttachmentTest(TestCase):
    def setUp(self):
        self.bartender = Bartender.objects.create(
            name="Foo", username="foo", email="foo@example.com"
        )
        self.expense = OutOfPocketExpense.objects.create(
            bartender=self.bartender,
            bank_registration_number="1234",
            bank_account_number="1234567890",
        )
        self.item = OutOfPocketExpenseItem.objects.create(
            expense=self.expense, description="Lunch", amount="123.45"
        )

    @override_settings(
        S3_REGION_NAME="eu-west-1",
        EXPENSE_ATTACHMENT_BUCKET_NAME="expense-attachments",
    )
    @patch("accountant.services.boto3.client")
    def test_uploads_file_to_s3(self, boto3_client):
        s3_client = boto3_client.return_value

        class FakeFile:
            name = "receipt.png"
            content_type = "image/png"

            def read(self):
                return b"fake-image-bytes"

        object_key = upload_expense_attachment(FakeFile(), self.item)

        boto3_client.assert_called_once_with(
            "s3",
            endpoint_url="http://localhost:9000",
            aws_access_key_id="minioadmin",
            aws_secret_access_key="minioadmin",
            region_name="eu-west-1",
        )
        s3_client.put_object.assert_called_once()
        _, kwargs = s3_client.put_object.call_args
        self.assertEqual(kwargs["Bucket"], "expense-attachments")
        self.assertEqual(kwargs["Body"], b"fake-image-bytes")
        self.assertEqual(kwargs["ContentType"], "image/png")
        self.assertTrue(
            object_key.startswith(
                f"expense-attachments/{self.expense.id}/{self.item.id}/"
            )
        )
        self.assertTrue(object_key.endswith("-receipt.png"))


class AddExpenseAdminViewTest(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(
            username="staff", password="password", is_staff=True
        )
        self.bartender = Bartender.objects.create(
            name="Foo", username="foo", email="foo@example.com"
        )

    def test_requires_staff_login(self):
        response = self.client.get(reverse(ADD_EXPENSE_URL_NAME))
        self.assertNotEqual(response.status_code, 200)

    @patch("accountant.admin.upload_expense_attachment")
    def test_creates_expense_with_items_and_attachments(self, upload_mock):
        upload_mock.return_value = "expense-attachments/1/1/receipt.png"

        self.client.force_login(self.staff_user)
        receipt = SimpleUploadedFile(
            "receipt.png", b"fake-bytes", content_type="image/png"
        )

        response = self.client.post(
            reverse(ADD_EXPENSE_URL_NAME),
            {
                "bartender": self.bartender.pk,
                "bank_registration_number": "1234",
                "bank_account_number": "1234567890",
                "items-TOTAL_FORMS": "1",
                "items-INITIAL_FORMS": "0",
                "items-MIN_NUM_FORMS": "0",
                "items-MAX_NUM_FORMS": "1000",
                "items-0-description": "Taxi",
                "items-0-amount": "99.50",
                "items-0-notes": "",
                "items-0-attachments": receipt,
            },
        )

        self.assertEqual(response.status_code, 200)
        expense = OutOfPocketExpense.objects.get(bartender=self.bartender)
        item = expense.items.get(description="Taxi")
        self.assertEqual(str(item.amount), "99.50")
        upload_mock.assert_called_once()
        self.assertEqual(ExpenseAttachment.objects.filter(expense_item=item).count(), 1)
        self.assertEqual(
            ExpenseAttachment.objects.get(expense_item=item).s3_object_key,
            "expense-attachments/1/1/receipt.png",
        )


class ExpenseAdminReadOnlyTest(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="admin", password="password", email="admin@example.com"
        )
        self.bartender = Bartender.objects.create(
            name="Foo", username="foo", email="foo@example.com"
        )
        self.expense = OutOfPocketExpense.objects.create(
            bartender=self.bartender,
            bank_registration_number="1234",
            bank_account_number="1234567890",
        )
        self.item = OutOfPocketExpenseItem.objects.create(
            expense=self.expense, description="Taxi", amount="99.50"
        )
        self.attachment = ExpenseAttachment.objects.create(
            expense_item=self.item,
            s3_object_key="expense-attachments/1/1/receipt.png",
        )
        self.client.force_login(self.superuser)

    def test_changelist_shows_total_amount(self):
        response = self.client.get(
            reverse("admin:accountant_outofpocketexpense_changelist")
        )
        self.assertContains(response, "99.50 DKK")

    def test_change_view_is_read_only_without_complete_expenses_permission(self):
        viewer = User.objects.create_user(
            username="viewer", password="password", is_staff=True
        )
        viewer.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="accountant", codename="view_outofpocketexpense"
            ),
            Permission.objects.get(
                content_type__app_label="accountant",
                codename="view_outofpocketexpenseitem",
            ),
            Permission.objects.get(
                content_type__app_label="accountant", codename="view_expenseattachment"
            ),
        )
        self.client.force_login(viewer)

        response = self.client.get(
            reverse(
                "admin:accountant_outofpocketexpense_change", args=[self.expense.pk]
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'name="_save"')
        self.assertNotContains(response, 'name="completed"')
        self.assertContains(response, "Taxi")
        self.assertContains(response, "receipt.png")

    def test_change_view_allows_editing_completed_with_permission(self):
        completer = User.objects.create_user(
            username="completer", password="password", is_staff=True
        )
        completer.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="accountant", codename="view_outofpocketexpense"
            ),
            Permission.objects.get(
                content_type__app_label="accountant",
                codename="view_outofpocketexpenseitem",
            ),
            Permission.objects.get(
                content_type__app_label="accountant", codename="view_expenseattachment"
            ),
            Permission.objects.get(
                content_type__app_label="accountant", codename="complete_expenses"
            ),
        )
        self.client.force_login(completer)

        response = self.client.get(
            reverse(
                "admin:accountant_outofpocketexpense_change", args=[self.expense.pk]
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="_save"')
        self.assertContains(response, 'name="completed"')

        from django.contrib import admin as django_admin
        from django.test import RequestFactory

        request = RequestFactory().get("/")
        request.user = completer
        model_admin = django_admin.site._registry[OutOfPocketExpense]
        self.assertTrue(model_admin.has_change_permission(request))
        self.assertNotIn(
            "completed", model_admin.get_readonly_fields(request, self.expense)
        )

    def test_cannot_edit_completed_without_permission(self):
        viewer = User.objects.create_user(
            username="viewer2", password="password", is_staff=True
        )
        viewer.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="accountant", codename="view_outofpocketexpense"
            )
        )
        self.client.force_login(viewer)

        response = self.client.post(
            reverse(
                "admin:accountant_outofpocketexpense_change", args=[self.expense.pk]
            ),
            {
                "bartender": self.bartender.pk,
                "bank_registration_number": "1234",
                "bank_account_number": "1234567890",
                "completed": "on",
                "_save": "Save",
            },
        )
        self.assertEqual(response.status_code, 403)
        self.expense.refresh_from_db()
        self.assertFalse(self.expense.completed)

    @patch("accountant.admin.build_expense_attachment_download_url")
    def test_download_redirects_to_presigned_url(self, build_url_mock):
        build_url_mock.return_value = "https://example.com/presigned-receipt.png"

        response = self.client.get(
            reverse(
                "admin:accountant_expenseattachment_download",
                args=[self.attachment.pk],
            )
        )

        self.assertRedirects(
            response,
            "https://example.com/presigned-receipt.png",
            fetch_redirect_response=False,
        )
        build_url_mock.assert_called_once_with(self.attachment)

    def test_download_shows_error_when_bucket_not_configured(self):
        response = self.client.get(
            reverse(
                "admin:accountant_expenseattachment_download",
                args=[self.attachment.pk],
            )
        )

        self.assertRedirects(
            response,
            reverse(
                "admin:accountant_outofpocketexpense_change", args=[self.expense.pk]
            ),
        )


class BuildExpenseAttachmentDownloadUrlTest(TestCase):
    def setUp(self):
        self.bartender = Bartender.objects.create(
            name="Foo", username="foo", email="foo@example.com"
        )
        self.expense = OutOfPocketExpense.objects.create(
            bartender=self.bartender,
            bank_registration_number="1234",
            bank_account_number="1234567890",
        )
        self.item = OutOfPocketExpenseItem.objects.create(
            expense=self.expense, description="Taxi", amount="99.50"
        )
        self.attachment = ExpenseAttachment.objects.create(
            expense_item=self.item,
            s3_object_key="expense-attachments/1/1/receipt.png",
        )

    @override_settings(
        S3_REGION_NAME="eu-west-1",
        EXPENSE_ATTACHMENT_BUCKET_NAME="expense-attachments",
        EXPENSE_ATTACHMENT_PRESIGNED_URL_EXPIRATION=600,
    )
    @patch("accountant.services.boto3.client")
    def test_builds_presigned_url(self, boto3_client):
        s3_client = boto3_client.return_value
        s3_client.generate_presigned_url.return_value = (
            "https://example.com/receipt.png"
        )

        url = build_expense_attachment_download_url(self.attachment)

        self.assertEqual(url, "https://example.com/receipt.png")
        s3_client.generate_presigned_url.assert_called_once_with(
            "get_object",
            Params={
                "Bucket": "expense-attachments",
                "Key": "expense-attachments/1/1/receipt.png",
                "ResponseContentDisposition": 'attachment; filename="receipt.png"',
            },
            ExpiresIn=600,
        )
