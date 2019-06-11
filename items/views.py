from django.views.generic import ListView
from .models import Item


class Items(ListView):
    template_name = "items.html"
    allow_empty = True
    model = Item
    context_object_name = 'items'
    ordering = ('name',)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        items_data = []
        for item in Item.objects.all():
            items_data.append({
                'brewery': item.brewery.name if item.brewery else None,
                'name': item.name,
                'price': item.priceInDKK,
                'barcode': item.barcode,
                'id': item.id,
            })

        context['items_data'] = items_data

        return context


class Search(ListView):
    template_name = "search.html"
    allow_empty = True
    model = Item
    context_object_name = 'items'
