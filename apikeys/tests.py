from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.views import APIView

from apikeys.models import GranularAPIKey
from apikeys.permissions import GranularPermission


class GranularAPIKeyAuthenticationTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def test_bearer_api_key_populates_request_auth(self):
        from apikeys.authentication import GranularAPIKeyAuthentication

        api_key, secret_key = GranularAPIKey.objects.create_key(name="Test Key")
        request = self.factory.get("/", HTTP_AUTHORIZATION=f"Bearer {secret_key}")

        view = APIView()
        view.authentication_classes = (GranularAPIKeyAuthentication,)

        drf_request = view.initialize_request(request)

        self.assertEqual(drf_request.auth, api_key)

    def test_missing_bearer_header_returns_no_authentication(self):
        from apikeys.authentication import GranularAPIKeyAuthentication

        request = self.factory.get("/")

        authenticator = GranularAPIKeyAuthentication()

        self.assertIsNone(authenticator.authenticate(request))


class ExplicitPermissionView(APIView):
    required_permissions = ("items.add_brewery",)


class GranularPermissionTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(
            username="permission-user", password="take_a_break"
        )

    def test_explicit_required_permissions_apply_to_authenticated_users(self):
        request = self.factory.get("/")
        force_authenticate(request, user=self.user)

        view = ExplicitPermissionView()
        drf_request = view.initialize_request(request)

        self.assertFalse(GranularPermission().has_permission(drf_request, view))

        self.user.user_permissions.add(Permission.objects.get(codename="add_brewery"))
        self.user = get_user_model().objects.get(pk=self.user.pk)
        request = self.factory.get("/")
        force_authenticate(request, user=self.user)
        drf_request = view.initialize_request(request)

        self.assertTrue(GranularPermission().has_permission(drf_request, view))
