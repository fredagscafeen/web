from django.utils import timezone
from django.views.generic import TemplateView

from events.models import Event
from items.models import Item


class Signage(TemplateView):
    template_name = "signage.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["beerOfTheMonth"] = Item.objects.filter(isBeerOfTheMonth=True).first()
        context["spotlightItems"] = Item.objects.filter(isOnSpotlight=True)

        events = Event.objects.select_related("event_album").prefetch_related(
            "links", "responses", "bartender_whitelist", "bartender_blacklist"
        )
        events = events.filter(
            event_type=Event.EventType.COMMON,
            start_datetime__gte=timezone.now(),
        ).order_by("start_datetime")
        context["events"] = events[:2]

        return context
