import os

from django import template

register = template.Library()


@register.filter("safe_crop_url")
def safe_crop_url(file_field, size_spec="940x940"):
    """
    Safely retrieves the cropped URL from a VersatileImageField.
    If the file is missing locally, returns None instead of crashing.
    """
    if not file_field:
        return None

    try:
        # Check if the file field has a name and exists on the disk
        if file_field.name and os.path.exists(file_field.path):
            # Access the 'crop' property dynamically
            crop_engine = getattr(file_field, "crop", None)
            if crop_engine:
                return crop_engine[size_spec].url
    except (FileNotFoundError, ValueError, AttributeError):
        pass

    # Return None so the template knows to fall back to the placeholder image
    return None
