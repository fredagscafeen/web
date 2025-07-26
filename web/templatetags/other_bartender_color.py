from django import template

register = template.Library()


@register.filter(name="other_bartender_color")
def other_bartender_color(shift, index):
    return shift.other_bartender_color(index)
