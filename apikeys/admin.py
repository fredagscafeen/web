from django.contrib import admin
from rest_framework_api_key.admin import APIKeyModelAdmin
from rest_framework_api_key.models import APIKey

from .models import GranularAPIKey

# Register your models here.

admin.site.unregister(APIKey)


@admin.action(description="Revoke selected API keys")
def revoke_api_keys(modeladmin, request, queryset):
    queryset.update(revoked=True)


@admin.action(description="Unrevoke selected API keys")
def unrevoke_api_keys(modeladmin, request, queryset):
    queryset.update(revoked=False)


@admin.action(description="Regenerate selected API keys")
def regenerate_api_keys(modeladmin, request, queryset):
    if queryset.count() > 1:
        modeladmin.message_user(
            request, "Please select only one API key to regenerate.", level="error"
        )
        return

    api_key = queryset.first()

    try:
        new_secret = api_key.regenerate_key()

        # Show the secret prominently to the user
        modeladmin.message_user(
            request,
            f"New secret for '{api_key.name}': {new_secret}. STORE THIS SAFELY, IT WILL NOT BE SHOWN AGAIN.",
            level="warning",
        )
    except Exception as e:
        modeladmin.message_user(request, f"Error: {str(e)}", level="error")


@admin.register(GranularAPIKey)
class GranularAPIKeyAdmin(APIKeyModelAdmin):
    actions = [revoke_api_keys, unrevoke_api_keys, regenerate_api_keys]
    title = "Granular API Keys"
    filter_horizontal = ("allowed_permissions",)

    list_display = ("name", "created", "expiry_date", "revoked")
    list_filter = ("created", "expiry_date", "revoked")

    def get_readonly_fields(self, request, obj=None):
        # Return the fields you want to be read-only
        return ("prefix", "hashed_key", "created")

    def get_fieldsets(self, request, obj=None):
        return (
            (None, {"fields": ("name", "allowed_permissions")}),
            (
                "API Key Details",
                {
                    "fields": (
                        "prefix",
                        "hashed_key",
                        "created",
                        "expiry_date",
                        "revoked",
                    ),
                    "classes": ("collapse",),  # Keeps the library stuff tidy
                },
            ),
        )
