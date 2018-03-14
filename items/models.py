from django.db import models

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
    priceInDKK = models.FloatField(default=0.0)
    abv = models.FloatField(null=True, blank=True)
    container = models.CharField(choices=CONTAINER, blank=True, max_length=140)
    volumeInCentiliters = models.IntegerField(null=True, blank=True)
    inStock = models.BooleanField(default=True)
    imageUrl = models.CharField(max_length=255, blank=True)
    barcode = models.CharField(max_length=255, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    lastModified = models.DateTimeField(auto_now=True, null=True, blank=True)
    link = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.brewery.__str__() + ' - ' + self.name


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
