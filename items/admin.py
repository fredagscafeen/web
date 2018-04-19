from django.contrib import admin

from items.models import Item, BeerType, Brewery


class ItemAdmin(admin.ModelAdmin):
    list_display = ('brewery', 'name')
    search_fields = ('brewery__name', 'name')
    list_display_links = ('name',)
    list_filter = ('container', 'type', 'brewery',)
    empty_value_display = ''
    ordering = ('name',)

    ordered_related_fields_to_model = {
        'brewery': Brewery,
        'type': BeerType,
    }

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """ Makes querysets for brewery and type fields ordered by name """

        try:
            model = self.ordered_related_fields_to_model[db_field.name]
            kwargs['queryset'] = model.objects.order_by('name')
        except KeyError:
            pass

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class BeerTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    ordering = ('name',)


class BreweryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    ordering = ('name',)


admin.site.register(Item, ItemAdmin)
admin.site.register(BeerType, BeerTypeAdmin)
admin.site.register(Brewery, BreweryAdmin)
