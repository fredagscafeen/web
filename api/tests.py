import uuid
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apikeys.models import GranularAPIKey
from items.models import Brewery, Item
from mail.models import ForwardedMail, IncomingMail, MailArchive, MailingList


class ApiTests(APITestCase):
    password = "take_a_break"
    api_key_counter = 0

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="yeaah", password=self.password
        )

    def authenticate(self, token=None, permissions=None):
        if not token:
            self.api_key_counter += 1
            # Create the key instance
            api_key, key = GranularAPIKey.objects.create_key(
                name=f"Test Key {self.api_key_counter}"
            )
            token = key

            # If specific permissions are requested for this test, add them
            if permissions:
                for permission_codename in permissions:
                    perm = Permission.objects.get(codename=permission_codename)
                    api_key.allowed_permissions.add(perm)

        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % token)

    def create_brewery(self, name):
        return self.client.post(reverse("breweries-list"), {"name": name})

    def api_path(self, suffix):
        return f"/{settings.LANGUAGE_CODE}/api/{suffix}"

    def test_read_access_anonymous(self):
        r = self.client.get(reverse("items-list"))
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_add_brewery_anonymous(self):
        r = self.create_brewery("Hancock")
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_add_brewery_authenticated_no_permissions(self):
        self.authenticate()
        r = self.create_brewery("Hancock")
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_add_brewery_authenticated_with_permissions(self):
        self.authenticate(permissions=["add_brewery"])
        r = self.create_brewery("Hancock")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Brewery.objects.exists())

    def test_last_modified_view(self):
        b = Brewery.objects.create(name="Aarhus Bryghus")
        item = Item.objects.create(name="Forårsbryg", priceInDKK=15)

        r = self.client.get(reverse("last-modified"))
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data, item.lastModified)

        r = self.client.post(reverse("last-modified"))
        self.assertEqual(r.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        self.authenticate()
        r = self.client.get(reverse("last-modified"))
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    @patch("api.views.Printer.get_status", return_value=("done", None))
    def test_print_status_requires_api_key_permission(self, mocked_get_status):
        self.authenticate()
        r = self.client.get(reverse("print_status", kwargs={"job_id": "123"}))
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)
        mocked_get_status.assert_not_called()

        self.authenticate(permissions=["view_printer"])
        r = self.client.get(reverse("print_status", kwargs={"job_id": "123"}))
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data, {"status": "done", "code": None})
        mocked_get_status.assert_called_once_with("123")

    def test_bad_token(self):
        self.authenticate("invalidtoken")
        r = self.client.get(reverse("breweries-list"))
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

        # deauth
        self.client.credentials()
        r = self.client.get(reverse("breweries-list"))
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_monitoring_ingest_requires_api_key_permission(self):
        payload = {
            "request_uuid": str(uuid.uuid4()),
            "received_at": timezone.now().isoformat(),
            "sender": "sender@example.com",
            "target": "best@fredagscafeen.dk",
            "status": IncomingMail.Status.PROCESSED,
            "s3_object_key": "archive/test.eml",
            "expanded_recipients": ["one@example.com"],
        }

        r = self.client.post(
            self.api_path("monitoring/incoming-mails/"),
            payload,
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

        self.authenticate()
        r = self.client.post(
            self.api_path("monitoring/incoming-mails/"),
            payload,
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_monitoring_ingest_upserts_processed_mail_and_is_idempotent(self):
        mailing_list = MailingList.objects.create(name="best")
        request_uuid = uuid.uuid4()
        received_at = timezone.now()
        payload = {
            "request_uuid": str(request_uuid),
            "received_at": received_at.isoformat(),
            "sender": "sender@example.com",
            "target": "best@fredagscafeen.dk",
            "mailing_list": mailing_list.name,
            "status": IncomingMail.Status.PROCESSED,
            "reason": "",
            "s3_object_key": "archive/request-1.eml",
            "expanded_recipients": ["one@example.com", "two@example.com"],
        }

        self.authenticate(permissions=["add_incomingmail", "change_incomingmail"])
        first_response = self.client.post(
            self.api_path("monitoring/incoming-mails/"),
            payload,
            format="json",
        )
        self.assertEqual(first_response.status_code, status.HTTP_200_OK)

        payload["sender"] = "updated@example.com"
        payload["expanded_recipients"] = ["two@example.com", "three@example.com"]
        second_response = self.client.post(
            self.api_path("monitoring/incoming-mails/"),
            payload,
            format="json",
        )
        self.assertEqual(second_response.status_code, status.HTTP_200_OK)

        self.assertEqual(MailArchive.objects.count(), 1)
        self.assertEqual(IncomingMail.objects.count(), 1)
        self.assertEqual(ForwardedMail.objects.count(), 2)

        archive = MailArchive.objects.get(request_uuid=request_uuid)
        incoming_mail = IncomingMail.objects.get(mail_archive=archive)
        self.assertEqual(archive.s3_object_key, "archive/request-1.eml")
        self.assertEqual(incoming_mail.sender, "updated@example.com")
        self.assertEqual(incoming_mail.target, "best@fredagscafeen.dk")
        self.assertEqual(incoming_mail.mailing_list, mailing_list)
        self.assertEqual(incoming_mail.status, IncomingMail.Status.PROCESSED)
        self.assertEqual(
            list(
                incoming_mail.forward_attempts.order_by("target").values_list(
                    "target", "status", "reason"
                )
            ),
            [
                ("three@example.com", ForwardedMail.Status.FORWARDED, ""),
                ("two@example.com", ForwardedMail.Status.FORWARDED, ""),
            ],
        )
        self.assertEqual(
            set(
                incoming_mail.forward_attempts.values_list("forwarded_at", flat=True)
            ),
            {received_at},
        )

    def test_monitoring_ingest_creates_dropped_mail_without_forwarded_rows(self):
        request_uuid = uuid.uuid4()
        payload = {
            "request_uuid": str(request_uuid),
            "received_at": timezone.now().isoformat(),
            "sender": "sender@example.com",
            "target": "unknown@fredagscafeen.dk",
            "status": IncomingMail.Status.DROPPED,
            "reason": "No matching mailing list",
            "s3_object_key": "archive/request-2.eml",
            "expanded_recipients": [],
        }

        self.authenticate(permissions=["add_incomingmail", "change_incomingmail"])
        response = self.client.post(
            self.api_path("monitoring/incoming-mails/"),
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        incoming_mail = IncomingMail.objects.get(mail_archive__request_uuid=request_uuid)
        self.assertEqual(incoming_mail.status, IncomingMail.Status.DROPPED)
        self.assertEqual(incoming_mail.reason, "No matching mailing list")
        self.assertEqual(incoming_mail.forward_attempts.count(), 0)

    def test_monitoring_ingest_upserting_dropped_mail_removes_initial_forwarded_rows(self):
        request_uuid = uuid.uuid4()
        received_at = timezone.now()
        processed_payload = {
            "request_uuid": str(request_uuid),
            "received_at": received_at.isoformat(),
            "sender": "sender@example.com",
            "target": "best@fredagscafeen.dk",
            "status": IncomingMail.Status.PROCESSED,
            "reason": "",
            "s3_object_key": "archive/request-2.eml",
            "expanded_recipients": ["one@example.com", "two@example.com"],
        }
        dropped_payload = {
            **processed_payload,
            "status": IncomingMail.Status.DROPPED,
            "reason": "Suppressed after ingest",
            "expanded_recipients": [],
        }

        self.authenticate(permissions=["add_incomingmail", "change_incomingmail"])
        processed_response = self.client.post(
            self.api_path("monitoring/incoming-mails/"),
            processed_payload,
            format="json",
        )
        self.assertEqual(processed_response.status_code, status.HTTP_200_OK)

        dropped_response = self.client.post(
            self.api_path("monitoring/incoming-mails/"),
            dropped_payload,
            format="json",
        )
        self.assertEqual(dropped_response.status_code, status.HTTP_200_OK)

        incoming_mail = IncomingMail.objects.get(mail_archive__request_uuid=request_uuid)
        self.assertEqual(incoming_mail.status, IncomingMail.Status.DROPPED)
        self.assertEqual(incoming_mail.reason, "Suppressed after ingest")
        self.assertEqual(incoming_mail.forward_attempts.count(), 0)

    def test_forwarded_mail_status_patch_requires_api_key_permission(self):
        forwarded_mail = ForwardedMail.objects.create(
            incoming_mail=IncomingMail.objects.create(
                received_at=timezone.now(),
                sender="sender@example.com",
                target="best@fredagscafeen.dk",
                mail_archive=MailArchive.objects.create(
                    request_uuid=uuid.uuid4(),
                    s3_object_key="archive/request-3.eml",
                ),
                status=IncomingMail.Status.PROCESSED,
            ),
            target="member@example.com",
            forwarded_at=timezone.now(),
            status=ForwardedMail.Status.FORWARDED,
        )

        self.authenticate()
        response = self.client.patch(
            self.api_path(f"monitoring/forwarded-mails/{forwarded_mail.pk}/"),
            {"status": ForwardedMail.Status.FAILED, "reason": "SMTP timeout"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        forwarded_mail.refresh_from_db()
        self.assertEqual(forwarded_mail.status, ForwardedMail.Status.FORWARDED)

    def test_forwarded_mail_status_patch_marks_mail_as_failed(self):
        forwarded_mail = ForwardedMail.objects.create(
            incoming_mail=IncomingMail.objects.create(
                received_at=timezone.now(),
                sender="sender@example.com",
                target="best@fredagscafeen.dk",
                mail_archive=MailArchive.objects.create(
                    request_uuid=uuid.uuid4(),
                    s3_object_key="archive/request-4.eml",
                ),
                status=IncomingMail.Status.PROCESSED,
            ),
            target="member@example.com",
            forwarded_at=timezone.now(),
            status=ForwardedMail.Status.FORWARDED,
        )

        self.authenticate(permissions=["change_forwardedmail"])
        response = self.client.patch(
            self.api_path(f"monitoring/forwarded-mails/{forwarded_mail.pk}/"),
            {"status": ForwardedMail.Status.FAILED, "reason": "SMTP timeout"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        forwarded_mail.refresh_from_db()
        self.assertEqual(forwarded_mail.status, ForwardedMail.Status.FAILED)
        self.assertEqual(forwarded_mail.reason, "SMTP timeout")

    def test_forwarded_mail_status_patch_requires_failure_reason(self):
        forwarded_mail = ForwardedMail.objects.create(
            incoming_mail=IncomingMail.objects.create(
                received_at=timezone.now(),
                sender="sender@example.com",
                target="best@fredagscafeen.dk",
                mail_archive=MailArchive.objects.create(
                    request_uuid=uuid.uuid4(),
                    s3_object_key="archive/request-5.eml",
                ),
                status=IncomingMail.Status.PROCESSED,
            ),
            target="member@example.com",
            forwarded_at=timezone.now(),
            status=ForwardedMail.Status.FORWARDED,
        )

        self.authenticate(permissions=["change_forwardedmail"])
        response = self.client.patch(
            self.api_path(f"monitoring/forwarded-mails/{forwarded_mail.pk}/"),
            {"status": ForwardedMail.Status.FAILED},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("reason", response.data)
