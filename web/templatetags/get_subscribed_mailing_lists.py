from django import template

from mail.models import MailingList

register = template.Library()


@register.filter(name="get_subscribed_mailing_lists")
def get_subscribed_mailing_lists(bartender):
    """
    Returns a list of mailing lists the user is subscribed to.
    """
    return MailingList.objects.filter(members=bartender).order_by("name")
