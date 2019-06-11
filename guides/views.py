from django.views.generic import TemplateView
from .models import Guide


class Guides(TemplateView):
    template_name = "guides.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        guides = []
        for k, name in Guide.GUIDE_TYPES:
            guides.append((name, Guide.objects.filter(category=k)))

        context['guides'] = guides

        return context
