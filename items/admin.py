from django.contrib import admin

from items.models import Item, BeerType, Brewery


@admin.register(Item)
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


@admin.register(BeerType)
class BeerTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    ordering = ('name',)


@admin.register(Brewery)
class BreweryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    ordering = ('name',)
