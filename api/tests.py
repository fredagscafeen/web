from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.urls import reverse

from items.models import Brewery, Item
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase


class ApiTests(APITestCase):
    password = "take_a_break"

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="yeaah", password=self.password
        )

    def authenticate(self, token=None):
        if not token:
            token = Token.objects.get_or_create(user=self.user)[0].key
        self.client.credentials(HTTP_AUTHORIZATION="Token %s" % token)

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
        self.authenticate()
        self.user.user_permissions.add(Permission.objects.get(codename="add_brewery"))
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

    def test_get_authentication_token(self):
        r = self.client.post(
            reverse("token-auth"),
            {"username": self.user.username, "password": self.password,},
        )

        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIn("permissions", r.data)
        self.assertIn("token", r.data)

        # Test that we can use the token
        # A 403 means we don't have permission, would have been 401 if not authenticated
        self.authenticate(r.data["token"])
        r = self.create_brewery("Humlebryg")  # coming soon #3050
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

        r = self.client.post(
            reverse("token-auth"),
            {"username": self.user.username, "password": "xXLegitPasswordXx",},
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bad_token(self):
        self.authenticate("invalidtoken")
        r = self.client.get(reverse("breweries-list"))
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

        # deauth
        self.client.credentials()
        r = self.client.get(reverse("breweries-list"))
        self.assertEqual(r.status_code, status.HTTP_200_OK)
