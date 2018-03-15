from django.contrib import admin

from items.models import Item, BeerType, Brewery


class ItemAdmin(admin.ModelAdmin):
    list_display = ('brewery', 'name')
    search_fields = ('brewery', 'name')
    list_display_links = ('name',)
    list_filter = ('container', 'type', 'brewery',)
    empty_value_display = ''
    ordering = ('name',)


class BeerTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)


class BreweryAdmin(admin.ModelAdmin):
    list_display = ('name',)


admin.site.register(Item, ItemAdmin)
admin.site.register(BeerType, BeerTypeAdmin)
admin.site.register(Brewery, BreweryAdmin)
