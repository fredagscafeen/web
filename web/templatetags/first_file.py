from django import template

register = template.Library()


@register.filter("first_file")
def first_file(album):
    if not album:
        return None
    start_file = album.basemedia.all().select_subclasses().first()
    return start_file
