import datetime
import zipfile
from io import BytesIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import ExpenseAttachment, OutOfPocketExpense, OutOfPocketExpenseItem
from .services import build_expense_attachment_download_url, upload_expense_attachment

User = get_user_model()

ADD_EXPENSE_URL_NAME = "admin:accountant_add_out_of_pocket_expense_changelist"


def nested_attachment_management(item_index, total=0):
    prefix = f"items-{item_index}-attachments"
    return {
        f"{prefix}-TOTAL_FORMS": str(total),
        f"{prefix}-INITIAL_FORMS": str(total),
        f"{prefix}-MIN_NUM_FORMS": "0",
        f"{prefix}-MAX_NUM_FORMS": "1000",
    }


def view_permissions():
    return [
        Permission.objects.get(
            content_type__app_label="accountant", codename="view_outofpocketexpense"
        ),
        Permission.objects.get(
            content_type__app_label="accountant", codename="view_outofpocketexpenseitem"
        ),
        Permission.objects.get(
            content_type__app_label="accountant", codename="view_expenseattachment"
        ),
    ]


class UploadExpenseAttachmentTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="foo", password="password", is_staff=True
        )
        self.expense = OutOfPocketExpense.objects.create(
            user=self.user,
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
                "user": self.staff_user.pk,
                "bank_registration_number": "1234",
                "bank_account_number": "1234567890",
                "items-TOTAL_FORMS": "2",
                "items-INITIAL_FORMS": "0",
                "items-MIN_NUM_FORMS": "0",
                "items-MAX_NUM_FORMS": "1000",
                "items-0-description": "Taxi",
                "items-0-date": "2026-08-30",
                "items-0-amount": "99.50",
                "items-0-notes": "",
                "items-0-attachments": receipt,
                "items-1-description": "Lunch",
                "items-1-date": "2026-08-31",
                "items-1-amount": "45.00",
                "items-1-notes": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        expense = OutOfPocketExpense.objects.get(user=self.staff_user)
        self.assertEqual(expense.items.count(), 2)
        item = expense.items.get(description="Taxi")
        self.assertEqual(str(item.amount), "99.50")
        self.assertEqual(item.date, datetime.date(2026, 8, 30))
        upload_mock.assert_called_once()
        self.assertEqual(ExpenseAttachment.objects.filter(expense_item=item).count(), 1)
        self.assertEqual(
            ExpenseAttachment.objects.get(expense_item=item).s3_object_key,
            "expense-attachments/1/1/receipt.png",
        )


class ExpenseAdminPermissionsTest(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="admin", password="password", email="admin@example.com"
        )
        self.creator = User.objects.create_user(
            username="creator", password="password", is_staff=True
        )
        self.expense = OutOfPocketExpense.objects.create(
            user=self.creator,
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

    def test_changelist_shows_total_amount(self):
        self.client.force_login(self.superuser)
        response = self.client.get(
            reverse("admin:accountant_outofpocketexpense_changelist")
        )
        self.assertContains(response, "99.50 DKK")

    def test_stranger_gets_read_only_view(self):
        stranger = User.objects.create_user(
            username="stranger", password="password", is_staff=True
        )
        stranger.user_permissions.add(*view_permissions())
        self.client.force_login(stranger)

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

    def test_creator_can_edit_until_completed(self):
        self.client.force_login(self.creator)

        response = self.client.get(
            reverse(
                "admin:accountant_outofpocketexpense_change", args=[self.expense.pk]
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="_save"')
        self.assertContains(response, 'name="bank_registration_number"')
        self.assertNotContains(response, 'name="completed"')

        self.expense.completed = True
        self.expense.save()

        response = self.client.get(
            reverse(
                "admin:accountant_outofpocketexpense_change", args=[self.expense.pk]
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'name="_save"')

    def test_completer_can_only_toggle_completed(self):
        completer = User.objects.create_user(
            username="completer", password="password", is_staff=True
        )
        completer.user_permissions.add(
            *view_permissions(),
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
        self.assertNotContains(response, 'name="bank_registration_number"')

        response = self.client.post(
            reverse(
                "admin:accountant_outofpocketexpense_change", args=[self.expense.pk]
            ),
            {
                "completed": "on",
                "items-TOTAL_FORMS": "1",
                "items-INITIAL_FORMS": "1",
                "items-MIN_NUM_FORMS": "0",
                "items-MAX_NUM_FORMS": "1000",
                "items-0-id": self.item.pk,
                **nested_attachment_management(0, total=1),
                "_save": "Save",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.expense.refresh_from_db()
        self.assertTrue(self.expense.completed)

    def test_stranger_cannot_post_changes(self):
        stranger = User.objects.create_user(
            username="stranger2", password="password", is_staff=True
        )
        stranger.user_permissions.add(*view_permissions())
        self.client.force_login(stranger)

        response = self.client.post(
            reverse(
                "admin:accountant_outofpocketexpense_change", args=[self.expense.pk]
            ),
            {
                "user": self.creator.pk,
                "bank_registration_number": "9999",
                "bank_account_number": "1234567890",
                "completed": "on",
                "_save": "Save",
            },
        )
        self.assertEqual(response.status_code, 403)
        self.expense.refresh_from_db()
        self.assertFalse(self.expense.completed)
        self.assertEqual(self.expense.bank_registration_number, "1234")

    def test_creator_can_add_extra_item(self):
        self.client.force_login(self.creator)

        response = self.client.post(
            reverse(
                "admin:accountant_outofpocketexpense_change", args=[self.expense.pk]
            ),
            {
                "user": self.creator.pk,
                "bank_registration_number": "1234",
                "bank_account_number": "1234567890",
                "items-TOTAL_FORMS": "2",
                "items-INITIAL_FORMS": "1",
                "items-MIN_NUM_FORMS": "0",
                "items-MAX_NUM_FORMS": "1000",
                "items-0-id": self.item.pk,
                "items-0-description": "Taxi",
                "items-0-date": "2026-08-30",
                "items-0-amount": "99.50",
                "items-0-notes": "",
                "items-1-description": "New item",
                "items-1-date": "2026-08-31",
                "items-1-amount": "10.00",
                "items-1-notes": "",
                **nested_attachment_management(0, total=0),
                **nested_attachment_management(1, total=0),
                "_save": "Save",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.expense.refresh_from_db()
        self.assertEqual(self.expense.items.count(), 2)
        self.assertTrue(self.expense.items.filter(description="New item").exists())

    @patch("accountant.admin.upload_expense_attachment")
    def test_creator_can_add_attachment_to_existing_item(self, upload_mock):
        upload_mock.return_value = "expense-attachments/1/1/new-receipt.png"
        self.client.force_login(self.creator)
        receipt = SimpleUploadedFile(
            "new-receipt.png", b"fake-bytes", content_type="image/png"
        )

        response = self.client.post(
            reverse(
                "admin:accountant_outofpocketexpense_change", args=[self.expense.pk]
            ),
            {
                "user": self.creator.pk,
                "bank_registration_number": "1234",
                "bank_account_number": "1234567890",
                "items-TOTAL_FORMS": "1",
                "items-INITIAL_FORMS": "1",
                "items-MIN_NUM_FORMS": "0",
                "items-MAX_NUM_FORMS": "1000",
                "items-0-id": self.item.pk,
                "items-0-description": "Taxi",
                "items-0-date": "2026-08-30",
                "items-0-amount": "99.50",
                "items-0-notes": "",
                "items-0-attachments": receipt,
                **nested_attachment_management(0, total=0),
                "_save": "Save",
            },
        )
        self.assertEqual(response.status_code, 302)
        upload_mock.assert_called_once()
        self.assertEqual(
            ExpenseAttachment.objects.filter(expense_item=self.item).count(), 2
        )

    @patch("accountant.admin.build_expense_attachment_download_url")
    def test_download_redirects_to_presigned_url(self, build_url_mock):
        self.client.force_login(self.superuser)
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
        self.client.force_login(self.superuser)
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

    @patch("accountant.admin.get_expense_attachment_bytes")
    @patch("accountant.admin.generate_pdf")
    def test_download_bundle_returns_zip(self, generate_pdf_mock, get_bytes_mock):
        self.client.force_login(self.superuser)

        def fake_generate_pdf(work_dir, context):
            path = f"{work_dir}/voucher.pdf"
            with open(path, "wb") as f:
                f.write(b"%PDF-1.4 fake")
            return path

        generate_pdf_mock.side_effect = fake_generate_pdf
        get_bytes_mock.return_value = b"fake receipt bytes"

        response = self.client.get(
            reverse(
                "admin:accountant_outofpocketexpense_bundle", args=[self.expense.pk]
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/zip")
        self.assertIn(f"udgiftsbilag-{self.expense.pk}.zip", response["Content-Disposition"])

        archive = zipfile.ZipFile(BytesIO(response.content))
        self.assertEqual(
            set(archive.namelist()),
            {f"udgiftsbilag-{self.expense.pk}.pdf", "bilag/receipt.png"},
        )
        self.assertEqual(archive.read(f"udgiftsbilag-{self.expense.pk}.pdf"), b"%PDF-1.4 fake")
        self.assertEqual(archive.read("bilag/receipt.png"), b"fake receipt bytes")

    @patch("accountant.admin.generate_pdf")
    def test_download_bundle_shows_error_when_bucket_not_configured(self, generate_pdf_mock):
        self.client.force_login(self.superuser)

        def fake_generate_pdf(work_dir, context):
            path = f"{work_dir}/voucher.pdf"
            with open(path, "wb") as f:
                f.write(b"%PDF-1.4 fake")
            return path

        generate_pdf_mock.side_effect = fake_generate_pdf

        response = self.client.get(
            reverse(
                "admin:accountant_outofpocketexpense_bundle", args=[self.expense.pk]
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
        self.user = User.objects.create_user(
            username="foo", password="password", is_staff=True
        )
        self.expense = OutOfPocketExpense.objects.create(
            user=self.user,
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
