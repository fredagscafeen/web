from django import template

register = template.Library()


@register.filter(name="container")
def container(container_type):
    if container_type == "BOTTLE":
        return "Flaske"

    if container_type == "DRAFT":
        return "Fad"
