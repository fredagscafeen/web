from decimal import Decimal

from django.contrib import admin
from django.test import TestCase

from .admin import ItemAdmin
from .models import Item


class ItemAdminTest(TestCase):
    def test_item_admin_loads_dynamic_suggested_price_script(self):
        media = ItemAdmin(Item, admin.site).media

        self.assertIn("js/item_admin.js", media._js)

    def test_suggested_price_has_dynamic_update_target(self):
        item = Item(purchasePriceInDKK=Decimal("10.00"))

        rendered_price = ItemAdmin(Item, admin.site).suggested_selling_price(item)

        self.assertIn('id="suggested-selling-price"', rendered_price)
        self.assertIn("15", rendered_price)
