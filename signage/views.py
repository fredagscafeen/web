from django.views.generic import TemplateView

from items.models import Item


class Signage(TemplateView):
    template_name = "signage.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["beerOfTheMonth"] = Item.objects.filter(isBeerOfTheMonth=True).first()
        context["spotlightItems"] = Item.objects.filter(isOnSpotlight=True)

        return context
