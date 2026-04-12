from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apikeys.models import GranularAPIKey
from items.models import Brewery, Item


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
