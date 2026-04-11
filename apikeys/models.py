from django.contrib.auth.models import Permission
from django.db import models
from django.utils import timezone
from rest_framework_api_key.models import AbstractAPIKey, BaseAPIKeyManager

from .crypto import CustomAPIKeyGenerator

# Create your models here.


class GranularAPIKeyManager(BaseAPIKeyManager):
    key_generator = CustomAPIKeyGenerator()


class GranularAPIKey(AbstractAPIKey):
    objects = GranularAPIKeyManager()
    name = models.CharField(max_length=255, unique=True)
    allowed_permissions = models.ManyToManyField(
        Permission, blank=True, help_text="Permissions this API Key is granted."
    )

    class Meta:
        verbose_name = "API Key"
        verbose_name_plural = "API Keys"

    def regenerate_key(self):
        temp_key = GranularAPIKey(name=f"temp_{self.pk}")

        new_secret = GranularAPIKey.objects.assign_key(temp_key)

        self.prefix = temp_key.prefix
        self.hashed_key = temp_key.hashed_key

        if self.expiry_date and self.created:
            # Set new expiry to NOW + original duration
            self.expiry_date = timezone.now() + (self.expiry_date - self.created)
            self.created = timezone.now()  # Reset created to now for clarity

        self.save()

        return new_secret
