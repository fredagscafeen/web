from django.contrib import admin

# Register your models here.
from items.models import Item, BeerType, Brewery

admin.site.register(Item)
admin.site.register(BeerType)
admin.site.register(Brewery)
