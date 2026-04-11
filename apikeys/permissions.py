from rest_framework import permissions
from rest_framework_api_key.permissions import BaseHasAPIKey, KeyParser

from .models import GranularAPIKey


class BearerKeyParser(KeyParser):
    keyword = "Bearer"


class HasGranularAPIKey(BaseHasAPIKey):
    model = GranularAPIKey
    key_parser = BearerKeyParser()

    def has_permission(self, request, view):
        key = self.get_key(request)
        if key is None:
            return False
        if not self.model.objects.is_valid(key):
            return False

        api_key = self.model.objects.get_from_key(key)

        request.auth = api_key

        required_permissions = getattr(view, "required_permissions", [])
        if not required_permissions:
            return True  # No specific permissions required, so the API key is valid for this view

        # 6. Verify the M2M permissions
        return api_key.allowed_permissions.filter(
            codename__in=required_permissions
        ).count() == len(required_permissions)


class GranularPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        # 1. Handle API Key Authentication
        if isinstance(request.auth, GranularAPIKey):
            # If it's an API Key, check our Granular Logic
            required_perms = getattr(view, "required_permissions", [])
            if not required_perms:
                # If no specific perm is required, let them through
                return True
            return request.auth.allowed_permissions.filter(
                codename__in=required_perms
            ).exists()

        # 2. Handle User Authentication (Session/Basic/Token)
        # Fall back to standard Django DjangoModelPermissions
        return permissions.DjangoModelPermissionsOrAnonReadOnly().has_permission(
            request, view
        )
