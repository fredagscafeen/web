from udlejning.models import Udlejning
from udlejning.models import UdlejningGrill
from django.contrib import admin


class UdlejningAdmin(admin.ModelAdmin):
    list_display = ('dateFrom', 'whoReserved', 'in_charge')
    filter_horizontal = ('bartendersInCharge', )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('bartendersInCharge')

    def in_charge(self, obj):
        return ', '.join(obj.bartendersInCharge.values_list('username', flat=True))


admin.site.register(Udlejning, UdlejningAdmin)
admin.site.register(UdlejningGrill, UdlejningAdmin)
