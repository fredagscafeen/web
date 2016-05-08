from django.views.generic import TemplateView

from bartenders.models import Bartender, BoardMember
from items.models import Item


class Index(TemplateView):
    template_name = "index.html"


class Contact(TemplateView):
    template_name = "contact.html"


class BartenderList(TemplateView):
    template_name = "bartenders.html"

    def get_context_data(self, **kwargs):
        context = super(BartenderList, self).get_context_data(**kwargs)
        context['bartenders'] = Bartender.objects.filter(isActiveBartender=True)
        context['inactive_bartenders'] = Bartender.objects.filter(isActiveBartender=False)
        return context


class Barplan(TemplateView):
    template_name = "barplan.html"


class Items(TemplateView):
    template_name = "items.html"

    def get_context_data(self, **kwargs):
        context = super(Items, self).get_context_data(**kwargs)
        context['items'] = Item.objects.all()
        return context


class Foo(TemplateView):
    template_name = "foo.html"

    def get_context_data(self, **kwargs):
        context = super(Foo, self).get_context_data(**kwargs)
        context['items'] = Item.objects.all()
        return context


class Board(TemplateView):
    template_name = "board.html"

    def get_context_data(self, **kwargs):
        context = super(Board, self).get_context_data(**kwargs)
        context['boardmembers'] = BoardMember.objects.filter()
        return context
