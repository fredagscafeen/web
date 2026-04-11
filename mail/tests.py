import uuid
from unittest.mock import Mock, patch

from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import RequestFactory, TestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.utils import timezone

from mail.admin import ForwardedMailAdmin, IncomingMailAdmin
from mail.models import ForwardedMail, IncomingMail, MailArchive, MailingList
from mail.services import build_mail_archive_download_url, request_forwarded_mail_resend

User = get_user_model()


class MonitoringModelsTest(TestCase):
    def create_archive(self):
        return MailArchive.objects.create(
            request_uuid=uuid.uuid4(),
            s3_object_key="incoming-mails/raw-message.eml",
        )

    def create_incoming_mail(self, **overrides):
        defaults = {
            "received_at": timezone.now(),
            "sender": "sender@example.com",
            "target": "list@fredagscafeen.dk",
            "mail_archive": self.create_archive(),
            "status": IncomingMail.Status.PROCESSED,
            "reason": "",
        }
        defaults.update(overrides)
        return IncomingMail.objects.create(**defaults)

    def test_mail_archive_stores_request_uuid_and_s3_key(self):
        request_uuid = uuid.uuid4()

        archive = MailArchive.objects.create(
            request_uuid=request_uuid,
            s3_object_key="incoming-mails/1234.eml",
        )

        self.assertEqual(archive.request_uuid, request_uuid)
        self.assertEqual(archive.s3_object_key, "incoming-mails/1234.eml")
        self.assertIsNotNone(archive.created_at)

    def test_incoming_mail_can_be_dropped_without_forwarded_mail_rows(self):
        incoming_mail = self.create_incoming_mail(
            status=IncomingMail.Status.DROPPED,
            reason="No matching mailing list",
        )

        self.assertIsNone(incoming_mail.mailing_list)
        self.assertEqual(incoming_mail.forward_attempts.count(), 0)
        self.assertEqual(incoming_mail.status, IncomingMail.Status.DROPPED)

    def test_incoming_mail_uses_a_unique_archive(self):
        archive = self.create_archive()

        incoming_mail = self.create_incoming_mail(mail_archive=archive)

        self.assertEqual(archive.incoming_mail, incoming_mail)

        with self.assertRaises(IntegrityError):
            self.create_incoming_mail(mail_archive=archive)

    def test_incoming_mail_can_reference_mailing_list(self):
        mailing_list = MailingList.objects.create(name="best")

        incoming_mail = self.create_incoming_mail(mailing_list=mailing_list)

        self.assertEqual(incoming_mail.mailing_list, mailing_list)
        self.assertEqual(mailing_list.incoming_mails.get(), incoming_mail)

    def test_forwarded_mail_tracks_resend_history(self):
        incoming_mail = self.create_incoming_mail()
        first_attempt = ForwardedMail.objects.create(
            incoming_mail=incoming_mail,
            target="member@example.com",
            forwarded_at=timezone.now(),
            status=ForwardedMail.Status.FAILED,
            reason="SMTP timeout",
        )

        retry_attempt = ForwardedMail.objects.create(
            incoming_mail=incoming_mail,
            target="member@example.com",
            forwarded_at=timezone.now(),
            status=ForwardedMail.Status.BOUNCED,
            reason="Mailbox unavailable",
            previous_attempt=first_attempt,
        )

        self.assertEqual(incoming_mail.forward_attempts.count(), 2)
        self.assertEqual(retry_attempt.previous_attempt, first_attempt)
        self.assertEqual(list(first_attempt.retry_attempts.all()), [retry_attempt])

    def test_deleting_initial_forward_attempt_cascades_retry_chain(self):
        incoming_mail = self.create_incoming_mail()
        first_attempt = ForwardedMail.objects.create(
            incoming_mail=incoming_mail,
            target="member@example.com",
            forwarded_at=timezone.now(),
            status=ForwardedMail.Status.FAILED,
            reason="SMTP timeout",
        )
        retry_attempt = ForwardedMail.objects.create(
            incoming_mail=incoming_mail,
            target="member@example.com",
            forwarded_at=timezone.now(),
            status=ForwardedMail.Status.FORWARDED,
            previous_attempt=first_attempt,
        )

        first_attempt.delete()

        self.assertFalse(
            ForwardedMail.objects.filter(
                pk__in=[first_attempt.pk, retry_attempt.pk]
            ).exists()
        )

    def test_forwarded_mail_cannot_reference_itself_as_previous_attempt(self):
        attempt = ForwardedMail.objects.create(
            incoming_mail=self.create_incoming_mail(),
            target="member@example.com",
            forwarded_at=timezone.now(),
            status=ForwardedMail.Status.FAILED,
            reason="SMTP timeout",
        )

        with self.assertRaises(IntegrityError):
            ForwardedMail.objects.filter(pk=attempt.pk).update(previous_attempt=attempt)

    def test_forwarded_mail_save_rejects_self_as_previous_attempt(self):
        attempt = ForwardedMail.objects.create(
            incoming_mail=self.create_incoming_mail(),
            target="member@example.com",
            forwarded_at=timezone.now(),
            status=ForwardedMail.Status.FAILED,
            reason="SMTP timeout",
        )
        attempt.previous_attempt = attempt

        with self.assertRaises(ValidationError) as error:
            attempt.save()

        self.assertEqual(
            error.exception.message_dict["previous_attempt"],
            ["A forwarded mail cannot reference itself as previous attempt."],
        )

    def test_forwarded_mail_previous_attempt_must_belong_to_same_incoming_mail(self):
        first_incoming_mail = self.create_incoming_mail()
        second_incoming_mail = self.create_incoming_mail(
            target="other-list@fredagscafeen.dk"
        )
        first_attempt = ForwardedMail.objects.create(
            incoming_mail=first_incoming_mail,
            target="member@example.com",
            forwarded_at=timezone.now(),
            status=ForwardedMail.Status.FAILED,
            reason="SMTP timeout",
        )
        second_attempt = ForwardedMail.objects.create(
            incoming_mail=second_incoming_mail,
            target="member@example.com",
            forwarded_at=timezone.now(),
            status=ForwardedMail.Status.FAILED,
            reason="SMTP timeout",
        )

        with self.assertRaises(IntegrityError):
            ForwardedMail.objects.filter(pk=second_attempt.pk).update(
                previous_attempt=first_attempt
            )

    def test_forwarded_mail_create_rejects_previous_attempt_from_other_incoming_mail(
        self,
    ):
        first_incoming_mail = self.create_incoming_mail()
        second_incoming_mail = self.create_incoming_mail(
            target="other-list@fredagscafeen.dk"
        )
        first_attempt = ForwardedMail.objects.create(
            incoming_mail=first_incoming_mail,
            target="member@example.com",
            forwarded_at=timezone.now(),
            status=ForwardedMail.Status.FAILED,
            reason="SMTP timeout",
        )

        with self.assertRaises(ValidationError) as error:
            ForwardedMail.objects.create(
                incoming_mail=second_incoming_mail,
                target="member@example.com",
                forwarded_at=timezone.now(),
                status=ForwardedMail.Status.FAILED,
                reason="SMTP timeout",
                previous_attempt=first_attempt,
            )

        self.assertEqual(
            error.exception.message_dict["previous_attempt"],
            ["previous_attempt must belong to the same incoming mail."],
        )


class MonitoringServicesTest(TestCase):
    def create_archive(self):
        return MailArchive.objects.create(
            request_uuid=uuid.uuid4(),
            s3_object_key="archive/test-message.eml",
        )

    def create_incoming_mail(self):
        return IncomingMail.objects.create(
            received_at=timezone.now(),
            sender="sender@example.com",
            target="list@fredagscafeen.dk",
            mail_archive=self.create_archive(),
            status=IncomingMail.Status.PROCESSED,
        )

    @override_settings(
        MAIL_ARCHIVE_BUCKET_NAME="mail-archive",
        MAIL_ARCHIVE_AWS_REGION="eu-west-1",
        MAIL_ARCHIVE_PRESIGNED_URL_EXPIRATION=600,
    )
    @patch("mail.services.boto3.client")
    def test_build_mail_archive_download_url_uses_presigned_s3_url(self, boto3_client):
        s3_client = boto3_client.return_value
        s3_client.generate_presigned_url.return_value = (
            "https://download.example.com/mail.eml"
        )

        download_url = build_mail_archive_download_url(self.create_archive())

        self.assertEqual(download_url, "https://download.example.com/mail.eml")
        boto3_client.assert_called_once_with("s3", region_name="eu-west-1")
        s3_client.generate_presigned_url.assert_called_once_with(
            "get_object",
            Params={
                "Bucket": "mail-archive",
                "Key": "archive/test-message.eml",
            },
            ExpiresIn=600,
        )

    @override_settings(
        DATMAIL_CONTROL_URL="https://datmail.example.com/control/resend",
        DATMAIL_CONTROL_TOKEN="shared-secret",
        DATMAIL_CONTROL_TIMEOUT=15,
    )
    @patch("mail.services.requests.post")
    def test_request_forwarded_mail_resend_posts_expected_payload(self, post):
        response = Mock()
        response.raise_for_status = Mock()
        post.return_value = response
        incoming_mail = self.create_incoming_mail()
        forwarded_mail = ForwardedMail.objects.create(
            incoming_mail=incoming_mail,
            target="member@example.com",
            forwarded_at=timezone.now(),
            status=ForwardedMail.Status.FAILED,
            reason="SMTP timeout",
        )

        request_forwarded_mail_resend(forwarded_mail)

        post.assert_called_once_with(
            "https://datmail.example.com/control/resend",
            json={
                "request_uuid": str(incoming_mail.mail_archive.request_uuid),
                "incoming_mail_id": incoming_mail.pk,
                "forwarded_mail_id": forwarded_mail.pk,
                "target": "member@example.com",
                "sender": "sender@example.com",
                "original_target": "list@fredagscafeen.dk",
            },
            headers={
                "Authorization": "Bearer shared-secret",
            },
            timeout=15,
        )
        response.raise_for_status.assert_called_once_with()


class IncomingMailAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = IncomingMailAdmin(IncomingMail, self.site)
        self.request_factory = RequestFactory()
        self.user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="password",
        )
        self.client.force_login(self.user)

    def create_archive(self):
        return MailArchive.objects.create(
            request_uuid=uuid.uuid4(),
            s3_object_key="archive/test-message.eml",
        )

    def create_incoming_mail(self, **overrides):
        defaults = {
            "received_at": timezone.now(),
            "sender": "sender@example.com",
            "target": "list@fredagscafeen.dk",
            "mail_archive": self.create_archive(),
            "status": IncomingMail.Status.PROCESSED,
            "reason": "",
        }
        defaults.update(overrides)
        return IncomingMail.objects.create(**defaults)

    def create_forwarded_mail(self, incoming_mail, **overrides):
        defaults = {
            "incoming_mail": incoming_mail,
            "target": "member@example.com",
            "forwarded_at": timezone.now(),
            "status": ForwardedMail.Status.FORWARDED,
            "reason": "",
        }
        defaults.update(overrides)
        return ForwardedMail.objects.create(**defaults)

    def test_changelist_defaults_to_processed_rows(self):
        processed = self.create_incoming_mail(sender="processed@example.com")
        dropped = self.create_incoming_mail(
            sender="dropped@example.com",
            status=IncomingMail.Status.DROPPED,
            reason="No matching mailing list",
        )

        response = self.client.get(reverse("admin:mail_incomingmail_changelist"))

        self.assertContains(response, processed.sender)
        self.assertNotContains(response, dropped.sender)

    def test_changelist_can_filter_dropped_rows(self):
        processed = self.create_incoming_mail(sender="processed@example.com")
        dropped = self.create_incoming_mail(
            sender="dropped@example.com",
            status=IncomingMail.Status.DROPPED,
            reason="No matching mailing list",
        )

        response = self.client.get(
            reverse("admin:mail_incomingmail_changelist"),
            {"status": IncomingMail.Status.DROPPED},
        )

        self.assertContains(response, dropped.sender)
        self.assertNotContains(response, processed.sender)

    def test_get_queryset_reports_deliverability_counts_from_latest_attempts(self):
        incoming_mail = self.create_incoming_mail()
        first_failed_attempt = self.create_forwarded_mail(
            incoming_mail,
            target="a@example.com",
            status=ForwardedMail.Status.FAILED,
            reason="SMTP timeout",
        )
        self.create_forwarded_mail(
            incoming_mail,
            target="a@example.com",
            status=ForwardedMail.Status.FORWARDED,
            previous_attempt=first_failed_attempt,
        )
        self.create_forwarded_mail(
            incoming_mail,
            target="b@example.com",
            status=ForwardedMail.Status.BOUNCED,
            reason="Mailbox unavailable",
        )

        request = self.request_factory.get(
            reverse("admin:mail_incomingmail_changelist")
        )
        request.user = self.user
        object_from_queryset = self.admin.get_queryset(request).get(pk=incoming_mail.pk)

        self.assertEqual(object_from_queryset.current_forwarded_count, 1)
        self.assertEqual(object_from_queryset.current_failed_count, 0)
        self.assertEqual(object_from_queryset.current_bounced_count, 1)
        self.assertTrue(object_from_queryset.has_resends)

    @override_settings(
        MAIL_ARCHIVE_BUCKET_NAME="mail-archive",
        MAIL_ARCHIVE_AWS_REGION="eu-west-1",
        MAIL_ARCHIVE_PRESIGNED_URL_EXPIRATION=600,
    )
    @patch("mail.admin.build_mail_archive_download_url")
    def test_download_eml_action_redirects_to_presigned_url(self, build_download_url):
        build_download_url.return_value = "https://download.example.com/mail.eml"
        incoming_mail = self.create_incoming_mail()

        response = self.client.get(
            reverse(
                "admin:mail_incomingmail_actions",
                kwargs={"pk": incoming_mail.pk, "tool": "download_eml"},
            )
        )

        self.assertRedirects(
            response,
            "https://download.example.com/mail.eml",
            fetch_redirect_response=False,
        )
        build_download_url.assert_called_once_with(incoming_mail.mail_archive)

    @patch("mail.admin.request_forwarded_mail_resend")
    def test_resend_action_requests_retry_for_current_failed_and_bounced_leaves(
        self, request_resend
    ):
        incoming_mail = self.create_incoming_mail()
        first_failed_attempt = self.create_forwarded_mail(
            incoming_mail,
            target="a@example.com",
            status=ForwardedMail.Status.FAILED,
            reason="SMTP timeout",
        )
        retried_successfully = self.create_forwarded_mail(
            incoming_mail,
            target="a@example.com",
            status=ForwardedMail.Status.FORWARDED,
            previous_attempt=first_failed_attempt,
        )
        self.create_forwarded_mail(
            incoming_mail,
            target="b@example.com",
            status=ForwardedMail.Status.FAILED,
            reason="Temporary failure",
        )
        current_bounced = self.create_forwarded_mail(
            incoming_mail,
            target="c@example.com",
            status=ForwardedMail.Status.BOUNCED,
            reason="Mailbox unavailable",
        )

        response = self.client.get(
            reverse(
                "admin:mail_incomingmail_actions",
                kwargs={"pk": incoming_mail.pk, "tool": "resend"},
            )
        )

        self.assertRedirects(
            response,
            reverse("admin:mail_incomingmail_change", args=[incoming_mail.pk]),
        )
        self.assertEqual(request_resend.call_count, 2)
        request_resend.assert_any_call(current_bounced)
        request_resend.assert_any_call(
            ForwardedMail.objects.get(
                target="b@example.com", previous_attempt__isnull=True
            )
        )
        self.assertNotIn(
            ((retried_successfully,), {}),
            request_resend.call_args_list,
        )

    @patch("mail.admin.request_forwarded_mail_resend")
    def test_resend_action_reports_partial_successes_and_errors(self, request_resend):
        incoming_mail = self.create_incoming_mail()
        self.create_forwarded_mail(
            incoming_mail,
            target="success@example.com",
            status=ForwardedMail.Status.FAILED,
            reason="SMTP timeout",
        )
        self.create_forwarded_mail(
            incoming_mail,
            target="failure@example.com",
            status=ForwardedMail.Status.BOUNCED,
            reason="Mailbox unavailable",
        )
        request_resend.side_effect = [None, RuntimeError("Datmail unavailable")]

        response = self.client.get(
            reverse(
                "admin:mail_incomingmail_actions",
                kwargs={"pk": incoming_mail.pk, "tool": "resend"},
            ),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(request_resend.call_count, 2)
        messages = [str(message) for message in get_messages(response.wsgi_request)]
        self.assertIn("Queued resend for 1 recipient(s).", messages)
        self.assertIn("Datmail unavailable", messages)

    def test_change_view_shows_forwarded_mail_inline(self):
        incoming_mail = self.create_incoming_mail()
        forwarded_mail = self.create_forwarded_mail(
            incoming_mail,
            target="inline@example.com",
            status=ForwardedMail.Status.FAILED,
            reason="SMTP timeout",
        )

        response = self.client.get(
            reverse("admin:mail_incomingmail_change", args=[incoming_mail.pk])
        )

        self.assertContains(response, forwarded_mail.target)
        self.assertContains(response, forwarded_mail.reason)


class ForwardedMailAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = ForwardedMailAdmin(ForwardedMail, self.site)
        self.user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="password",
        )
        self.client.force_login(self.user)

    def create_forwarded_mail(self, **overrides):
        incoming_mail = IncomingMail.objects.create(
            received_at=timezone.now(),
            sender="sender@example.com",
            target="list@fredagscafeen.dk",
            mail_archive=MailArchive.objects.create(
                request_uuid=uuid.uuid4(),
                s3_object_key="archive/test-message.eml",
            ),
            status=IncomingMail.Status.PROCESSED,
        )
        defaults = {
            "incoming_mail": incoming_mail,
            "target": "member@example.com",
            "forwarded_at": timezone.now(),
            "status": ForwardedMail.Status.FAILED,
            "reason": "SMTP timeout",
        }
        defaults.update(overrides)
        return ForwardedMail.objects.create(**defaults)

    @patch("mail.admin.request_forwarded_mail_resend")
    def test_resend_action_triggers_datmail_request(self, request_resend):
        forwarded_mail = self.create_forwarded_mail()

        response = self.client.get(
            reverse(
                "admin:mail_forwardedmail_actions",
                kwargs={"pk": forwarded_mail.pk, "tool": "resend"},
            )
        )

        self.assertRedirects(
            response,
            reverse("admin:mail_forwardedmail_change", args=[forwarded_mail.pk]),
        )
        request_resend.assert_called_once_with(forwarded_mail)

    @patch("mail.admin.request_forwarded_mail_resend")
    def test_resend_action_reports_errors_instead_of_crashing(self, request_resend):
        forwarded_mail = self.create_forwarded_mail()
        request_resend.side_effect = RuntimeError("Datmail unavailable")

        response = self.client.get(
            reverse(
                "admin:mail_forwardedmail_actions",
                kwargs={"pk": forwarded_mail.pk, "tool": "resend"},
            ),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        request_resend.assert_called_once_with(forwarded_mail)
        messages = [str(message) for message in get_messages(response.wsgi_request)]
        self.assertIn("Datmail unavailable", messages)
