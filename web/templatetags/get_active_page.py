from django import template

register = template.Library()


@register.filter(name="get_active_page")
def get_active_page(path):
    path = path.split("/")
    return path[2] if len(path) > 2 else ""
