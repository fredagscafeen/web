import os

from django import template

register = template.Library()


@register.filter("event_image_url")
def event_image_url(event):
    """
    Returns the best available image URL for an event,
    safely handling missing local files.
    """
    if not event or not getattr(event, "event_album", None):
        return None

    album = event.event_album

    # 1. Check for primary thumbnail
    if album.thumbnail:
        try:
            return album.thumbnail.url
        except ValueError:
            pass

    # 2. Check for first file (Image type only)
    first_file = album.basemedia.all().select_subclasses().first()
    if first_file and getattr(first_file, "type", None) == "I":
        file_field = getattr(first_file, "file", None)
        if file_field and file_field.name:
            try:
                # Safe local check for versatileimagefield
                if os.path.exists(file_field.path):
                    return file_field.crop["940x940"].url
            except (FileNotFoundError, ValueError, AttributeError):
                pass

    return None
