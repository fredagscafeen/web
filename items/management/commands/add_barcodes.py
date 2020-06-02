import sys

from django.core.management.base import BaseCommand
from iterfzf import iterfzf

from items.models import Item


class Command(BaseCommand):
    help = "Add barcodes to items"

    def handle(self, *args, **options):
        string_to_item = {}
        for item in Item.objects.all():
            item_string = str(item)
            if item_string in string_to_item:
                print(f"WARNING: Duplicate item: {item_string}", file=sys.stderr)
                i = 2
                while True:
                    new_string = f"{item_string} ({i})"
                    if new_string in string_to_item:
                        i += 1
                        continue

                    item_string = new_string
                    break

            string_to_item[str(item)] = item

        item_strings = sorted(string_to_item.keys())

        while True:
            selected_string = iterfzf(item_strings, case_sensitive=False)

            if not selected_string:
                return

            print()
            print(selected_string)
            item = string_to_item[selected_string]
            item.barcode = input("Barcode: ")
            item.save()
