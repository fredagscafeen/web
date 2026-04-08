from django.contrib.auth import authenticate, get_user_model
from django.test import TestCase

from bartab.models import BarTabUser
from bartenders.models import Bartender
from email_auth.auth import EmailTokenBackend
from email_auth.models import EmailToken

User = get_user_model()


class EmailTokenBackendTests(TestCase):
    def test_authenticate_rejects_invalid_token(self):
        EmailToken.objects.create(email="bob@example.org", token="valid-token")

        user = authenticate(email="bob@example.org", token="invalid-token")

        self.assertIsNone(user)
        self.assertEqual(User.objects.count(), 0)

    def test_authenticate_is_case_insensitive_and_creates_lowercase_user(self):
        email_token = EmailToken.objects.create(
            email="bob@example.org", token="valid-token"
        )

        user = authenticate(email="BOB@EXAMPLE.ORG", token="valid-token")

        self.assertIsNotNone(user)
        self.assertEqual(user.email, "bob@example.org")
        self.assertEqual(user.username, "ZZZZZ_email_bob@example.org")

        email_token.refresh_from_db()
        self.assertNotEqual(email_token.token, "valid-token")

    def test_authenticate_reuses_existing_staff_user(self):
        existing_user = User.objects.create_user(
            username="admin",
            email="bob@example.org",
            password="67",
            is_staff=True,
        )
        email_token = EmailToken.objects.create(
            email="bob@example.org", token="valid-token"
        )

        user = authenticate(email="BOB@EXAMPLE.ORG", token="valid-token")

        self.assertEqual(user.pk, existing_user.pk)
        self.assertEqual(
            User.objects.filter(email__iexact="bob@example.org").count(), 1
        )

        email_token.refresh_from_db()
        self.assertNotEqual(email_token.token, "valid-token")


class EmailTokenBackendLookupTests(TestCase):
    def test_is_user_matches_supported_models_case_insensitively(self):
        User.objects.create_user(
            username="staff",
            email="staff@example.org",
            password="irrelevant",
        )
        Bartender.objects.create(
            name="Bob",
            username="bob",
            email="bartender@example.org",
        )
        BarTabUser.objects.create(name="Bar Tab", email="bartab@example.org")

        self.assertTrue(EmailTokenBackend.is_user("STAFF@EXAMPLE.ORG"))
        self.assertTrue(EmailTokenBackend.is_user("BARTENDER@EXAMPLE.ORG"))
        self.assertTrue(EmailTokenBackend.is_user("BARTAB@EXAMPLE.ORG"))
        self.assertFalse(EmailTokenBackend.is_user("missing@example.org"))
