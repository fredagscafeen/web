from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _

from fredagscafeen.admin import CustomModelAdmin
from qr.models import QRCode

# Register your models here.


@admin.register(QRCode)
class QRCodeAdmin(CustomModelAdmin):
    list_display = (
        "name",
        "slug",
        "destination",
        "scan_count",
        "is_active",
        "created_at",
        "updated_at",
    )
    list_filter = ("is_active", "created_at", "updated_at")
    search_fields = ("name", "slug", "destination")
    ordering = ("-created_at",)

    class Media:
        """Include custom JavaScript for the admin interface to handle slug preview and validation."""

        js = ("js/qr_slug_preview.js",)

    def changelist_view(self, request, extra_context=None):
        """Adds an explanation banner to the top of the main list view page."""
        messages.info(
            request,
            _(
                "Dynamic QR Codes: You can safely change the 'Destination URL' at any time. "
                "The printed QR code relies entirely on the 'Slug', which should remain unchanged once printed."
                " To create a QR Code with the slug use https://genqrcode.com"
            ),
        )
        return super().changelist_view(request, extra_context=extra_context)

    def add_view(self, request, form_url="", extra_context=None):
        """Adds an explanation banner to the 'Create New QR Code' form page."""
        messages.info(
            request,
            _(
                "Fill out the form below. Leave the slug descriptive but short slugs make the "
                "QR code easier for older phone cameras to scan."
            ),
        )
        return super().add_view(request, form_url, extra_context)
