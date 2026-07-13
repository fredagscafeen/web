import requests
from django.contrib import admin, messages
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.translation import gettext_lazy as _
from unfold.decorators import action

from fredagscafeen.admin import CustomModelAdmin
from fredagscafeen.settings.base import GEN_QR_CODE_API_KEY, GEN_QR_CODE_API_URL
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
    list_display_links = ("name", "slug")
    search_fields = ("name", "slug", "destination")
    ordering = ("-created_at",)

    actions_detail = ("generate_and_download_qr",)

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

    @action(
        description="Generate & Download QR",
        url_path="generate-qr",
    )
    def generate_and_download_qr(self, request, object_id):
        qrcode = self.get_object(request, object_id)

        if not qrcode:
            messages.error(request, "QR Code not found.")
            return HttpResponseRedirect(request.path)

        base_domain = request.build_absolute_uri(
            "/"
        )  # Get the base domain of the current request
        url = f"{base_domain.rstrip('/')}/qr/{qrcode.slug}"

        api_url = f"{GEN_QR_CODE_API_URL}/public/generate"
        headers = {
            "GenQRCode-apikey": GEN_QR_CODE_API_KEY,
            "Content-Type": "application/json",
        }
        payload = {
            "text": url,
            "type": 0,
            "style": 2,
            "inner_eye_style": 1,
            "outer_eye_style": 1,
            "width": 500,
            "height": 500,
            "imageformat": "svg",
        }

        try:
            response = requests.post(api_url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()

            django_response = HttpResponse(
                response.content,
                content_type=response.headers.get(
                    "Content-Type", "application/octet-stream"
                ),
            )
            django_response["Content-Disposition"] = (
                f'attachment; filename="qr-{qrcode.slug}.{payload.get("imageformat", "svg")}"'
            )

            django_response["HX-Redirect"] = request.build_absolute_uri()

            return django_response

        except requests.RequestException as e:
            messages.error(request, f"API Error generating QR code: {str(e)}")

            response = HttpResponseRedirect(request.META.get("HTTP_REFERER", "../"))
            response["HX-Redirect"] = request.META.get("HTTP_REFERER", "../")
            return response
