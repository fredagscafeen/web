from datetime import datetime
from datetime import timezone as datetime_timezone
from decimal import Decimal
from unittest.mock import patch

from django.contrib import admin
from django.test import TestCase
from django.utils import timezone

from .admin import ItemAdmin
from .models import InventoryEntry, InventorySnapshot, Item


class ItemModelTest(TestCase):
    def test_purchase_prices_are_calculated_from_excluding_vat_price(self):
        item = Item(
            purchasePriceInDKKExcludingVAT=Decimal("10.00"),
            priceInDKK=Decimal("25.00"),
        )

        self.assertEqual(item.purchasePriceInDKK, Decimal("12.50"))
        self.assertEqual(item.priceInDKKExcludingVAT, Decimal("20.00"))

    def test_suggested_selling_price_is_rounded_up_to_five_dkk(self):
        item = Item(
            purchasePriceInDKKExcludingVAT=Decimal("10.00"),
            priceInDKK=Decimal("25.00"),
        )

        self.assertEqual(item.suggestedSellingPriceInDKK, Decimal("20.00"))

    def test_price_properties_return_none_without_purchase_price(self):
        item = Item(priceInDKK=Decimal("25.00"))

        self.assertIsNone(item.purchasePriceInDKK)
        self.assertIsNone(item.suggestedSellingPriceInDKK)
        self.assertIsNone(item.actualProfit)

    def test_actual_profit_and_margin_are_calculated(self):
        item = Item(
            purchasePriceInDKKExcludingVAT=Decimal("10.00"),
            priceInDKK=Decimal("25.00"),
        )

        self.assertEqual(item.actualProfit, Decimal("10.63"))
        self.assertEqual(item.profitMargin, Decimal("100.00"))

    def test_computed_price_properties_are_limited_to_two_decimal_places(self):
        item = Item(
            purchasePriceInDKKExcludingVAT=Decimal("10.01"),
            priceInDKK=Decimal("25.01"),
        )

        self.assertEqual(item.purchasePriceInDKK, Decimal("12.51"))
        self.assertEqual(item.priceInDKKExcludingVAT, Decimal("20.01"))
        self.assertEqual(item.actualProfit, Decimal("10.63"))
        self.assertEqual(item.profitMargin, Decimal("99.90"))

    def test_actual_profit_margin_is_none_when_purchase_price_is_zero(self):
        item = Item(
            purchasePriceInDKKExcludingVAT=Decimal("0.00"),
            priceInDKK=Decimal("25.00"),
        )

        self.assertIsNone(item.profitMargin)

    def test_current_amount_uses_the_latest_inventory_snapshot(self):
        item = Item.objects.create(name="Test item", priceInDKK=Decimal("25.00"))
        older_snapshot = InventorySnapshot.objects.create(
            datetime=datetime(2026, 1, 1, tzinfo=datetime_timezone.utc)
        )
        latest_snapshot = InventorySnapshot.objects.create(
            datetime=datetime(2026, 1, 2, tzinfo=datetime_timezone.utc)
        )
        InventoryEntry.objects.create(item=item, snapshot=older_snapshot, amount=2)
        InventoryEntry.objects.create(item=item, snapshot=latest_snapshot, amount=7)

        self.assertEqual(item.current_amount, 7)

    def test_current_amount_is_zero_without_inventory_entries(self):
        item = Item.objects.create(name="Test item", priceInDKK=Decimal("25.00"))

        self.assertEqual(item.current_amount, 0)

    def test_is_new_is_true_for_unpersisted_and_recent_items(self):
        now = datetime(2026, 1, 31, tzinfo=datetime_timezone.utc)

        with patch("items.models.timezone.now", return_value=now):
            self.assertTrue(Item(name="New item", priceInDKK=Decimal("25.00")).isNew)

            item = Item.objects.create(name="New item", priceInDKK=Decimal("25.00"))
            item.created = now - timezone.timedelta(days=29)
            self.assertTrue(item.isNew)

    def test_is_new_is_false_for_items_older_than_thirty_days(self):
        now = datetime(2026, 1, 31, tzinfo=datetime_timezone.utc)
        item = Item.objects.create(name="Old item", priceInDKK=Decimal("25.00"))
        item.created = now - timezone.timedelta(days=31)

        with patch("items.models.timezone.now", return_value=now):
            self.assertFalse(item.isNew)


class ItemAdminTest(TestCase):
    def test_profit_margin_column_is_orderable(self):
        item_admin = ItemAdmin(Item, admin.site)
        Item.objects.create(
            name="Low margin",
            purchasePriceInDKKExcludingVAT=Decimal("20.00"),
            priceInDKK=Decimal("25.00"),
        )
        Item.objects.create(
            name="High margin",
            purchasePriceInDKKExcludingVAT=Decimal("10.00"),
            priceInDKK=Decimal("25.00"),
        )
        Item.objects.create(name="No margin", priceInDKK=Decimal("25.00"))

        queryset = item_admin.get_queryset(None)

        self.assertEqual(ItemAdmin.profitMargin.admin_order_field, "profit_margin")
        self.assertEqual(
            list(queryset.order_by("profit_margin").values_list("name", flat=True)),
            ["No margin", "Low margin", "High margin"],
        )
        self.assertEqual(
            list(queryset.order_by("-profit_margin").values_list("name", flat=True)),
            ["High margin", "Low margin", "No margin"],
        )

    def test_item_admin_loads_dynamic_suggested_price_script(self):
        media = ItemAdmin(Item, admin.site).media

        self.assertIn("js/item_admin.js", media._js)

    def test_suggested_price_has_dynamic_update_target(self):
        item = Item(purchasePriceInDKKExcludingVAT=Decimal("10.00"))

        rendered_price = ItemAdmin(Item, admin.site).suggested_selling_price(item)

        self.assertIn('id="suggested-selling-price"', rendered_price)
        self.assertIn("20", rendered_price)

    def test_computed_readonly_fields_have_dynamic_update_targets(self):
        item = Item(
            purchasePriceInDKKExcludingVAT=Decimal("10.00"),
            priceInDKK=Decimal("25.00"),
        )
        item_admin = ItemAdmin(Item, admin.site)

        rendered_fields = {
            "purchasePriceInDKK": item_admin.purchasePriceInDKK(item),
            "priceInDKKExcludingVAT": item_admin.priceInDKKExcludingVAT(item),
            "actualProfit": item_admin.actualProfit(item),
            "profitMargin": item_admin.profitMargin(item),
        }

        expected_targets = {
            "purchasePriceInDKK": "purchase-price",
            "priceInDKKExcludingVAT": "price-excluding-vat",
            "actualProfit": "actual-profit",
            "profitMargin": "profit-margin",
        }
        for field_name, target_id in expected_targets.items():
            with self.subTest(field_name=field_name):
                self.assertIn(f'id="{target_id}"', rendered_fields[field_name])
