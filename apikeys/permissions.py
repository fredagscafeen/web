from rest_framework import permissions
from rest_framework_api_key.permissions import KeyParser

from .models import GranularAPIKey


class BearerKeyParser(KeyParser):
    keyword = "Bearer"


class GranularPermission(permissions.BasePermission):
    model_permissions = permissions.DjangoModelPermissionsOrAnonReadOnly()

    def get_view_model(self, view):
        queryset = getattr(view, "queryset", None)
        if queryset is None and hasattr(view, "get_queryset"):
            queryset = view.get_queryset()
        return getattr(queryset, "model", None)

    def normalize_required_permissions(self, required_permissions, view):
        model = self.get_view_model(view)
        app_label = getattr(getattr(model, "_meta", None), "app_label", None)

        normalized_permissions = []
        for required_permission in required_permissions:
            if "." in required_permission or app_label is None:
                normalized_permissions.append(required_permission)
            else:
                normalized_permissions.append(f"{app_label}.{required_permission}")
        return tuple(normalized_permissions)

    def get_required_permissions(self, request, view):
        explicit_permissions = getattr(view, "required_permissions", None)
        if explicit_permissions is not None:
            return self.normalize_required_permissions(explicit_permissions, view)

        if request.method in permissions.SAFE_METHODS:
            return ()

        model = self.get_view_model(view)
        if model is None:
            return ()

        return tuple(
            self.model_permissions.get_required_permissions(request.method, model)
        )

    def has_api_key_permissions(self, api_key, required_permissions):
        allowed_permissions = {
            f"{permission.content_type.app_label}.{permission.codename}"
            for permission in api_key.allowed_permissions.select_related("content_type")
        }
        return all(
            required_permission in allowed_permissions
            for required_permission in required_permissions
        )

    def has_permission(self, request, view):
        explicit_permissions = getattr(view, "required_permissions", None)

        # 1. Handle API Key Authentication
        if isinstance(request.auth, GranularAPIKey):
            # If it's an API Key, check our Granular Logic
            required_perms = self.get_required_permissions(request, view)
            if not required_perms:
                # If no specific perm is required, let them through
                return True
            return self.has_api_key_permissions(request.auth, required_perms)

        # 2. Handle User Authentication (Session/Basic/Token)
        if explicit_permissions is not None:
            return bool(
                request.user
                and request.user.is_authenticated
                and request.user.has_perms(
                    self.normalize_required_permissions(explicit_permissions, view)
                )
            )

        # Fall back to standard Django DjangoModelPermissions
        return self.model_permissions.has_permission(request, view)
