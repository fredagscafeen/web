from django.views.generic import TemplateView


class Signage(TemplateView):
    template_name = "signage.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
