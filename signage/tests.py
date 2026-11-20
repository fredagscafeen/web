from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from events.models import Event
from items.models import BeerType, Brewery, Item
from signage.views import (
    EVENT_SLIDE_SECONDS,
    MAX_EVENT_SLIDES,
    MAX_PRODUCT_SLIDES,
    build_slides,
    event_slides,
    product_slides,
)


def product(name, label="selection"):
    return {
        "kind": "product",
        "item": name,
        "label": label,
        "seconds": 12,
    }


def event_slide(name):
    return {"kind": "event", "event": name, "seconds": EVENT_SLIDE_SECONDS}


class BuildSlidesTests(TestCase):
    def test_products_only(self):
        products = [product("a"), product("b")]

        self.assertEqual(build_slides(products, []), products)

    def test_events_are_spliced_in_between_products(self):
        products = [product(name) for name in "abcd"]
        events = [event_slide("e1"), event_slide("e2")]

        slides = build_slides(products, events)

        self.assertEqual(
            [slide["kind"] for slide in slides],
            ["product", "product", "event", "product", "product", "event"],
        )
        self.assertEqual(slides[2], events[0])
        self.assertEqual(slides[5], events[1])

    def test_event_still_shown_when_there_are_too_few_products(self):
        products = [product("a")]
        events = [event_slide("e1")]

        slides = build_slides(products, events)

        self.assertEqual([slide["kind"] for slide in slides], ["product", "event"])
        self.assertEqual(slides[1], events[0])

    def test_events_loop_when_there_are_many_products(self):
        products = [product(name) for name in "abcdef"]
        events = [event_slide("e1")]

        slides = build_slides(products, events)

        kinds = [slide["kind"] for slide in slides]
        self.assertEqual(kinds.count("product"), 6)
        self.assertEqual(kinds.count("event"), 3)
        self.assertEqual(slides[2], slides[5])
        self.assertEqual(slides[5], slides[8])
        self.assertEqual(kinds[-1], "event")

    def test_no_products_shows_events(self):
        events = [event_slide("e1"), event_slide("e2")]

        self.assertEqual(build_slides([], events), events)


class ProductSlidesTests(TestCase):
    def setUp(self):
        self.type = BeerType.objects.create(name="IPA")
        self.brewery = Brewery.objects.create(name="Testbryggeriet")

    def make_item(self, name, **kwargs):
        defaults = {
            "priceInDKK": 45,
            "type": self.type,
            "brewery": self.brewery,
        }
        defaults.update(kwargs)
        return Item.objects.create(name=name, **defaults)

    def test_beer_of_the_month_comes_first(self):
        self.make_item("Almindelig")
        self.make_item("Månedens", isBeerOfTheMonth=True)
        self.make_item("Spotlight", isOnSpotlight=True)

        slides = product_slides()

        self.assertEqual(slides[0]["item"].name, "Månedens")
        self.assertEqual(slides[0]["label"], "beer_of_the_month")
        self.assertEqual(slides[1]["item"].name, "Spotlight")
        self.assertEqual(slides[1]["label"], "spotlight")
        self.assertEqual(slides[2]["label"], "selection")

    def test_out_of_stock_items_are_skipped(self):
        self.make_item("På lager")
        self.make_item("Udsolgt", inStock=False)

        self.assertEqual(
            [slide["item"].name for slide in product_slides()], ["På lager"]
        )

    def test_product_slides_are_capped(self):
        for index in range(MAX_PRODUCT_SLIDES + 5):
            self.make_item(f"Øl {index}")

        self.assertEqual(len(product_slides()), MAX_PRODUCT_SLIDES)


class EventSlidesTests(TestCase):
    def make_event(self, name, start_in_days=3, **kwargs):
        start = timezone.now() + timedelta(days=start_in_days)
        return Event.objects.create(
            name=name,
            year=start.year,
            start_datetime=start,
            end_datetime=start + timedelta(hours=5),
            **kwargs,
        )

    def test_only_upcoming_public_events_are_shown(self):
        self.make_event("Fremtidig", event_type=Event.EventType.COMMON)
        self.make_event("Fortidig", start_in_days=-3, event_type=Event.EventType.COMMON)
        self.make_event("Bartender", event_type=Event.EventType.INTERNAL)

        self.assertEqual(
            [slide["event"].name for slide in event_slides()], ["Fremtidig"]
        )

    def test_event_slides_are_capped(self):
        for index in range(MAX_EVENT_SLIDES + 3):
            self.make_event(
                f"Event {index}",
                start_in_days=index + 1,
                event_type=Event.EventType.COMMON,
            )

        self.assertEqual(len(event_slides()), MAX_EVENT_SLIDES)


class SignageViewTests(TestCase):
    def setUp(self):
        self.item = Item.objects.create(name="Signage Øl", priceInDKK=50)
        start = timezone.now() + timedelta(days=2)
        self.event = Event.objects.create(
            name="Signage Event",
            year=start.year,
            start_datetime=start,
            end_datetime=start + timedelta(hours=4),
            event_type=Event.EventType.COMMON,
        )

    def test_renders_products_and_events(self):
        response = self.client.get(reverse("signage"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Signage Øl")
        self.assertContains(response, "Signage Event")
        self.assertEqual(
            [slide["kind"] for slide in response.context["slides"]],
            ["product", "event"],
        )

    def test_empty_signage_still_renders(self):
        Item.objects.all().delete()
        Event.objects.all().delete()

        response = self.client.get(reverse("signage"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["slides"], [])
        self.assertContains(response, "Der er ingen produkter eller events lige nu")


class InitialSlideTests(TestCase):
    def setUp(self):
        for index in range(3):
            Item.objects.create(name=f"Øl {index}", priceInDKK=40)

    def test_defaults_to_the_first_slide(self):
        response = self.client.get(reverse("signage"))

        self.assertEqual(response.context["initial_slide"], 0)
        self.assertContains(response, 'data-initial-slide="0"')

    def test_slide_parameter_picks_the_starting_slide(self):
        response = self.client.get(reverse("signage"), {"slide": 2})

        self.assertEqual(response.context["initial_slide"], 1)
        self.assertContains(response, 'data-initial-slide="1"')

    def test_out_of_range_slide_parameter_is_clamped(self):
        self.assertEqual(
            self.client.get(reverse("signage"), {"slide": 99}).context["initial_slide"],
            2,
        )
        self.assertEqual(
            self.client.get(reverse("signage"), {"slide": -4}).context["initial_slide"],
            0,
        )
        self.assertEqual(
            self.client.get(reverse("signage"), {"slide": "abc"}).context[
                "initial_slide"
            ],
            0,
        )
