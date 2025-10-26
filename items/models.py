from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_noop

class Item(models.Model):
    brewery = models.ForeignKey(
        "Brewery", on_delete=models.SET_NULL, null=True, blank=True
    )
    type = models.ForeignKey(
        "BeerType", on_delete=models.SET_NULL, null=True, blank=True
    )
    name = models.CharField(max_length=140)
    name_dk = models.CharField(max_length=140, null=True, blank=True)
    description = models.TextField(blank=True)
    country = models.CharField(blank=True, max_length=140)
    priceInDKK = models.DecimalField(max_digits=9 + 2, decimal_places=0)
    abv = models.FloatField(null=True, blank=True)
    container = models.CharField(null=True, blank=True, max_length=140)
    container_dk = models.CharField(null=True, blank=True, max_length=140)
    volumeInCentiliters = models.IntegerField(null=True, blank=True)
    inStock = models.BooleanField(default=True)
    glutenFree = models.BooleanField(default=False)
    nonAlcoholic = models.BooleanField(default=False)
    image = models.ImageField(upload_to="items", blank=True, null=True)
    barcode = models.CharField(max_length=255, unique=True, null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    lastModified = models.DateTimeField(auto_now=True, null=True, blank=True)
    link = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        if self.brewery:
            return f"{self.brewery} - {self.name}"
        return self.name

    def save(self, *args, **kwargs):
        # Ensure empty barcode is represented as NULL and not ''
        # to enforce the unique constraint
        if not self.barcode:
            self.barcode = None

        # Remove from shelves when going out of stock
        if self.pk:  # Only for existing items (not new ones)
            try:
                old_item = Item.objects.get(pk=self.pk)
                if old_item.inStock and not self.inStock:
                    # Import here to avoid circular import
                    from items.models import ShelfItem
                    ShelfItem.objects.filter(item=self).delete()
            except Item.DoesNotExist:
                pass

        super().save(*args, **kwargs)

    @property
    def current_amount(self):
        latest_entry = self.entries.order_by("-snapshot__datetime").first()
        if latest_entry:
            return latest_entry.amount
        else:
            return 0


class Shelf(models.Model):
    name = models.CharField(max_length=140)

    def __str__(self):
        return self.name

class ShelfItem(models.Model):
    shelf = models.ForeignKey(Shelf, on_delete=models.CASCADE, related_name='shelf_items')
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='shelf_items')
    order = models.PositiveIntegerField(default=0)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('order', 'item__name')
        unique_together = ('shelf', 'item')

    @property
    def glutenFree(self):
        return self.item.glutenFree

    @property
    def nonAlcoholic(self):
        return self.item.nonAlcoholic

class BeerType(models.Model):
    name = models.CharField(max_length=140)
    name_dk = models.CharField(max_length=140, null=True, blank=True)
    description = models.TextField(blank=True)
    link = models.CharField(blank=True, max_length=255)

    def __str__(self):
        return self.name


class Brewery(models.Model):
    name = models.CharField(max_length=140)
    description = models.TextField(blank=True)
    website = models.CharField(blank=True, max_length=255)

    class Meta:
        verbose_name_plural = "Breweries"

    def __str__(self):
        return self.name


class InventorySnapshot(models.Model):
    datetime = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return str(self.datetime)


class InventoryEntry(models.Model):
    amount = models.PositiveIntegerField()
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="entries")
    snapshot = models.ForeignKey(
        InventorySnapshot, on_delete=models.CASCADE, related_name="entries"
    )

    def __str__(self):
        return f"{self.item}: {self.amount}"
