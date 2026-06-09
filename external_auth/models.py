from django.db import models

# Create your models here.


class ServicePermission(models.Model):
    """
    A Model used solely for defining custom permissions for external services.
    This model is not meant to be used for storing any data, but rather to define permissions that can be assigned to users or groups in the Django admin interface.
    """

    class Meta:
        # This prevents Django from creating a database table for this model
        managed = False
        default_permissions = ()  # Disables default add/change/delete perms

        permissions = [
            ("view_traefik", "Can view Traefik Dashboard"),
            ("view_garage", "Can view Garage S3 WebUI"),
        ]
