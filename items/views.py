from constance import config
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, TemplateView

from .models import Fridge, Item


class Items(ListView):
    template_name = "items.html"
    allow_empty = True
    model = Item
    context_object_name = "items"
    ordering = ("brewery",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        fridges = (
            Fridge.objects.all()
            .prefetch_related("shelves__shelf_items__item__brewery")
            .filter(shelves__isnull=False)
            .distinct()
        )

        items_data = []
        if config.SHOW_LIST_SELECTION:
            for item in Item.objects.all():
                items_data.append(
                    {
                        "brewery": item.brewery.name if item.brewery else None,
                        "brewery_url": item.brewery.website
                        if item.brewery and item.brewery.website
                        else None,
                        "name": item.name,
                        "bestBefore": item.bestBefore,
                        "inStock": item.inStock,
                        "type": item.type,
                        "container": item.container,
                        "price": item.priceInDKK,
                        "barcode": item.barcode,
                        "id": item.id,
                        "amount": item.current_amount,
                        "image": item.image,
                    }
                )

        show_all = "show_all" in self.request.GET

        if not show_all:
            items_data = [d for d in items_data if d["inStock"]]

        context["show_all"] = show_all
        context["items_data"] = items_data
        context["fridges"] = fridges
        context["show_list_selection"] = config.SHOW_LIST_SELECTION

        return context


class Scanner(TemplateView):
    template_name = "scanner.html"
