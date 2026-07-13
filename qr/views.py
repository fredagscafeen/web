from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext as _

from .models import QRCode

# Create your views here.


def qr_redirect_view(request, slug):
    """
    View to handle redirection based on the QR code slug.
    This view looks up the QRCode model using the provided slug,
    increments the scan count, and redirects to the destination URL.
    """
    qr_code = get_object_or_404(QRCode, slug=slug)

    if not qr_code.is_active:
        raise Http404(_("QR code is not active."))

    qr_code.increment_scan_count()

    return redirect(qr_code.destination)
