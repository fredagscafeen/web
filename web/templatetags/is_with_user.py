from django import template

register = template.Library()


@register.filter(name='is_with_user')
def is_with_user(shift, user):
    if not user.is_authenticated:
        return False

    return shift.is_with_bartender(user.username)

