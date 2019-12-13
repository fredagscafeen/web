from django.core.management.base import BaseCommand
from items.models import Item, InventoryEntry, InventorySnapshot
import pytz
import datetime
import argparse
import csv
from collections import defaultdict


class Command(BaseCommand):
    help = "Imports inventory from a csv file"

    def add_arguments(self, parser):
        parser.add_argument("file", type=argparse.FileType("r"))

    def handle(self, *args, **options):
        assert options["file"].readline() == "\ufeffsep=,\n"

        rows = []
        for row in csv.DictReader(
            options["file"],
            ["id", "name", "diff", "datetime", "barcode", "unused_price"],
        ):
            try:
                row["item"] = Item.objects.get(id=int(row["id"]))
            except Item.DoesNotExist:
                try:
                    row["item"] = Item.objects.get(barcode=row["barcode"])
                except Item.DoesNotExist:
                    row["item"] = Item.objects.get(name=row["name"].split("  ")[1])

            row["diff"] = int(row["diff"])
            row["datetime"] = pytz.utc.localize(
                datetime.datetime.fromisoformat(row["datetime"])
            )
            rows.append(row)

        rows.sort(key=lambda r: r["datetime"])

        GROUPING_THRESHOLD = datetime.timedelta(minutes=30)

        amounts = defaultdict(int)
        groups = []
        prow = None
        diff_time = None
        pos = 0
        negs = 0
        for row in rows:
            if prow != None:
                diff_time = row["datetime"] - prow["datetime"]

            if prow == None or diff_time > GROUPING_THRESHOLD:
                print(diff_time)
                print('Positives:', pos)
                print('Negatives:', negs)
                groups.append((row["datetime"], {}))

                pos = 0
                negs = 0

            item = row["item"]
            amounts[item] += row["diff"]
            groups[-1][1][item] = amounts[item]

            pos += row["diff"] > 0
            negs += row["diff"] < 0

            prow = row

        InventorySnapshot.objects.all().delete()
        InventoryEntry.objects.all().delete()

        for dt, items in groups:
            snapshot = InventorySnapshot.objects.create(datetime=dt)

            for item, amount in items.items():
                InventoryEntry.objects.create(
                    snapshot=snapshot, item=item, amount=amount
                )
