import uuid

from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from mail.models import ForwardedMail, IncomingMail, MailArchive, MailingList


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
