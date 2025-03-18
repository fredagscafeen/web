from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, TemplateView

from .models import Item


class Items(ListView):
    template_name = "items.html"
    allow_empty = True
    model = Item
    context_object_name = "items"
    ordering = ("brewery",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        items_data = []
        for item in Item.objects.all():
            items_data.append(
                {
                    "brewery": item.brewery.name if item.brewery else None,
                    "brewery_url": item.brewery.website
                    if item.brewery and item.brewery.website
                    else None,
                    "name": item.name,
                    "name_dk": item.name_dk,
                    "inStock": item.inStock,
                    "type": item.type,
                    "container": item.container,
                    "container_dk": item.container_dk,
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

        return context


class Scanner(TemplateView):
    template_name = "scanner.html"
