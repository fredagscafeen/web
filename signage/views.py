import random

from django.utils import timezone
from django.views.generic import TemplateView

from events.models import Event
from items.models import Item

# How long each slide stays on the screen, in seconds.
PRODUCT_SLIDE_SECONDS = 12
EVENT_SLIDE_SECONDS = 15

# An event slide is shown after this many product slides.
PRODUCTS_BETWEEN_EVENTS = 2

# Upper bounds, so a long product list does not push events out of the loop.
MAX_PRODUCT_SLIDES = 14
MAX_EVENT_SLIDES = 4

BEER_OF_THE_MONTH_LABEL = "beer_of_the_month"
SPOTLIGHT_LABEL = "spotlight"
SELECTION_LABEL = "selection"


def product_slides():
    """Product slides, most promoted products first, the rest in random order."""
    items = list(Item.objects.filter(inStock=True).select_related("type", "brewery"))

    beer_of_the_month = [item for item in items if item.isBeerOfTheMonth][:1]
    spotlight = [
        item for item in items if item.isOnSpotlight and item not in beer_of_the_month
    ]
    rest = [
        item
        for item in items
        if item not in beer_of_the_month and item not in spotlight
    ]
    random.shuffle(rest)

    chosen = [(item, BEER_OF_THE_MONTH_LABEL) for item in beer_of_the_month] + [
        (item, SPOTLIGHT_LABEL) for item in spotlight
    ]
    chosen += [(item, SELECTION_LABEL) for item in rest]

    return [
        {
            "kind": "product",
            "item": item,
            "label": label,
            "seconds": PRODUCT_SLIDE_SECONDS,
        }
        for item, label in chosen[:MAX_PRODUCT_SLIDES]
    ]


def event_slides():
    """The next upcoming public events, one slide each."""
    events = (
        Event.objects.select_related("event_album")
        .prefetch_related("links")
        .filter(
            event_type=Event.EventType.COMMON,
            start_datetime__gte=timezone.now(),
        )
        .order_by("start_datetime")[:MAX_EVENT_SLIDES]
    )

    return [
        {"kind": "event", "event": event, "seconds": EVENT_SLIDE_SECONDS}
        for event in events
    ]


def build_slides(products, events):
    """Interleave events into the product loop, so both kinds keep appearing."""
    if not products:
        return list(events)

    slides = []
    events_shown = 0
    for index, product in enumerate(products, start=1):
        slides.append(product)
        if events and index % PRODUCTS_BETWEEN_EVENTS == 0:
            slides.append(events[events_shown % len(events)])
            events_shown += 1

    # Too few products for a full gap: still show one event before the loop restarts.
    if events and events_shown == 0:
        slides.append(events[0])

    return slides


class Signage(TemplateView):
    template_name = "signage.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        products = product_slides()
        events = event_slides()
        slides = build_slides(products, events)

        context["slides"] = slides
        context["product_slide_count"] = len(products)
        context["event_slide_count"] = len(events)
        context["initial_slide"] = initial_slide(self.request, len(slides))

        return context


def initial_slide(request, slide_count):
    """The slide the loop starts at. `?slide=3` pins it, mainly while adjusting the screen."""
    if slide_count == 0:
        return 0

    try:
        index = int(request.GET.get("slide", 1)) - 1
    except (TypeError, ValueError):
        index = 0

    return min(max(index, 0), slide_count - 1)
