from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

# Create your models here.


class QRCode(models.Model):
    id = models.AutoField(primary_key=True)
    slug = models.SlugField(
        unique=True,
        max_length=255,
        help_text=_(
            "A unique identifier for the QR code. If left blank, it will be generated from the name. <br>"
            "<strong>Live Link:</strong> <code class='loading-placeholder'>Generating preview...</code> <br>"
            "<em>Note: Once printed, the slug should not be changed, as the physical QR code relies on it.</em>"
        ),
    )
    name = models.CharField(
        max_length=255, help_text=_("A descriptive name for the QR code.")
    )
    destination = models.URLField(
        max_length=2000,
        help_text=_(
            "The URL that the QR code will redirect to when scanned. This should be a valid URL."
        ),
    )
    is_active = models.BooleanField(
        default=True, help_text=_("Whether the QR code is active and can be scanned.")
    )
    scan_count = models.PositiveIntegerField(
        default=0,
        help_text=_("The number of times the QR code has been scanned."),
        editable=False,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Dynamic QR-code")
        verbose_name_plural = _("Dynamic QR-codes")
        ordering = ["-created_at"]

    def increment_scan_count(self):
        """Increments the scan count by 1."""
        self.scan_count += 1
        self.save(update_fields=["scan_count"])

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        self.slug = self.slug.lower()
        super().save(*args, **kwargs)
