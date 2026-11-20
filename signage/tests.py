from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from events.models import Event
from items.models import (
    BeerType,
    Brewery,
    Fridge,
    FridgeShelfAssignment,
    Item,
    Shelf,
    ShelfItem,
)
from signage.views import (
    EVENT_SLIDE_SECONDS,
    MAX_EVENT_SLIDES,
    MAX_OVERVIEW_SPOTLIGHT_ITEMS,
    MAX_PRODUCT_SLIDES,
    SLIDES_PER_SELECTION,
    build_slides,
    event_slides,
    overview_slide,
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


def make_fridge(name="Køleskab"):
    return Fridge.objects.create(name=name)


def shelve(item, fridge=None):
    """Put an item on a shelf, in a fridge when one stands there, like the bar does."""
    shelf = Shelf.objects.create(name=f"Hylde {Shelf.objects.count() + 1}")
    ShelfItem.objects.create(shelf=shelf, item=item)
    if fridge is not None:
        FridgeShelfAssignment.objects.create(fridge=fridge, shelf=shelf)
    return item


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
        self.fridge = make_fridge()

    def make_item(self, name, shelved=True, fridge="default", **kwargs):
        defaults = {
            "priceInDKK": 45,
            "type": self.type,
            "brewery": self.brewery,
        }
        defaults.update(kwargs)
        item = Item.objects.create(name=name, **defaults)
        if shelved:
            shelve(item, self.fridge if fridge == "default" else fridge)
        return item

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

    def test_items_not_on_a_shelf_are_skipped(self):
        self.make_item("På hylde")
        self.make_item("Kun på lager", shelved=False)

        self.assertEqual(
            [slide["item"].name for slide in product_slides()], ["På hylde"]
        )

    def test_items_on_a_shelf_outside_a_fridge_are_skipped(self):
        self.make_item("I køleskab")
        self.make_item("Løs hylde", fridge=None)

        self.assertEqual(
            [slide["item"].name for slide in product_slides()], ["I køleskab"]
        )

    def test_item_on_two_shelves_only_gets_one_slide(self):
        item = self.make_item("To hylder")
        shelve(item, self.fridge)

        self.assertEqual(len(product_slides()), 1)


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
        self.item = shelve(
            Item.objects.create(name="Signage Øl", priceInDKK=50), make_fridge()
        )
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

    def test_page_is_never_cached(self):
        response = self.client.get(reverse("signage"))

        self.assertIn("no-store", response["Cache-Control"])
        self.assertIn("no-cache", response["Cache-Control"])

    def test_empty_page_reloads_itself_instead_of_freezing(self):
        Item.objects.all().delete()
        Event.objects.all().delete()

        response = self.client.get(reverse("signage"))

        self.assertEqual(len(response.context["slides"]), 0)
        self.assertContains(response, "lastAdvance")

    def test_selection_starts_over_after_22_slides(self):
        response = self.client.get(reverse("signage"))

        self.assertEqual(response.context["slides_per_selection"], SLIDES_PER_SELECTION)
        self.assertEqual(SLIDES_PER_SELECTION, 22)
        self.assertContains(response, 'data-refresh-after="22"')

    def test_empty_signage_still_renders(self):
        Item.objects.all().delete()
        Event.objects.all().delete()

        response = self.client.get(reverse("signage"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["slides"], [])
        self.assertContains(response, "Sortiment")


class InitialSlideTests(TestCase):
    def setUp(self):
        fridge = make_fridge()
        for index in range(3):
            shelve(Item.objects.create(name=f"Øl {index}", priceInDKK=40), fridge)

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


class OverviewSlideTests(TestCase):
    def setUp(self):
        self.type = BeerType.objects.create(name="IPA")
        fridge = make_fridge()
        self.spots = [
            shelve(
                Item.objects.create(
                    name=f"Spot {index}",
                    priceInDKK=40,
                    type=self.type,
                    isOnSpotlight=True,
                ),
                fridge,
            )
            for index in range(MAX_OVERVIEW_SPOTLIGHT_ITEMS + 2)
        ]
        self.beer = shelve(
            Item.objects.create(name="Månedens", priceInDKK=55, isBeerOfTheMonth=True),
            fridge,
        )

    def test_overview_repeats_the_promoted_products_and_the_next_events(self):
        start = timezone.now() + timedelta(days=3)
        created = [
            Event.objects.create(
                name=f"Event {index}",
                year=start.year,
                start_datetime=start,
                end_datetime=start + timedelta(hours=3),
                event_type=Event.EventType.COMMON,
            )
            for index in range(3)
        ]
        events = [{"kind": "event", "event": event, "seconds": 15} for event in created]

        overview = overview_slide(product_slides(), events)

        self.assertEqual(overview["kind"], "overview")
        self.assertEqual(overview["beer"], self.beer)
        self.assertEqual(len(overview["spotlight"]), MAX_OVERVIEW_SPOTLIGHT_ITEMS)
        self.assertEqual(
            [event.name for event in overview["events"]], ["Event 0", "Event 1"]
        )

    def test_overview_is_skipped_without_promoted_products(self):
        for item in self.spots + [self.beer]:
            item.isOnSpotlight = False
            item.isBeerOfTheMonth = False
            item.save()

        self.assertIsNone(overview_slide(product_slides(), []))

    def test_overview_is_the_first_slide(self):
        products = [product("a"), product("b")]
        overview = {
            "kind": "overview",
            "seconds": 20,
            "beer": None,
            "spotlight": [],
            "events": [],
        }

        slides = build_slides(products, [], overview)

        self.assertEqual(slides[0], overview)
        self.assertEqual(slides[1:], products)

    def test_view_starts_with_the_overview(self):
        response = self.client.get(reverse("signage"))

        self.assertEqual(response.context["slides"][0]["kind"], "overview")
        self.assertEqual(response.context["initial_slide"], 0)
