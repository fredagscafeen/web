from django.db import models
from django.utils import timezone

CONTAINER = (
    ('DRAFT', 'Fad'),  #0
    ('BOTTLE', 'Flaske'), #1
    ('SHOT', 'Shot'), #2
    ('FOOD', 'Madvare'), #3
    ('OTHER', 'Andet') #4
)


class Item(models.Model):
    brewery = models.ForeignKey("Brewery", on_delete=models.SET_NULL, null=True, blank=True)
    type = models.ForeignKey("BeerType", on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=140)
    description = models.TextField(blank=True)
    country = models.CharField(blank=True, max_length=140)
    priceInDKK = models.DecimalField(max_digits=9 + 2, decimal_places=2)
    abv = models.FloatField(null=True, blank=True)
    container = models.CharField(choices=CONTAINER, blank=True, max_length=140)
    volumeInCentiliters = models.IntegerField(null=True, blank=True)
    inStock = models.BooleanField(default=True)
    imageUrl = models.CharField(max_length=255, blank=True)
    barcode = models.CharField(max_length=255, unique=True, null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    lastModified = models.DateTimeField(auto_now=True, null=True, blank=True)
    link = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        if self.brewery:
            return f'{self.brewery} - {self.name}'
        return self.name

    def save(self, *args, **kwargs):
        # Ensure empty barcode is represented as NULL and not ''
        # to enforce the unique constraint
        if not self.barcode:
            self.barcode = None

        super().save(*args, **kwargs)

    @property
    def current_amount(self):
        latest_entry = self.entries.order_by('-snapshot__datetime').first()
        if latest_entry:
            return latest_entry.amount
        else:
            return 0


class BeerType(models.Model):
    name = models.CharField(max_length=140)
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
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='entries')
    snapshot = models.ForeignKey(InventorySnapshot, on_delete=models.CASCADE, related_name='entries')

    def __str__(self):
        return f"{self.item}: {self.amount}"
