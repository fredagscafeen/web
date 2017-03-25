from udlejning.models import Udlejning
from udlejning.models import UdlejningGrill
from django.contrib import admin


class UdlejningAdmin(admin.ModelAdmin):
    list_display = ('dateFrom', 'whoReserved', 'bartenderInCharge')


class UdlejningGrillAdmin(admin.ModelAdmin):
    list_display = ('dateFrom', 'whoReserved', 'bartenderInCharge')


admin.site.register(Udlejning, UdlejningAdmin)
admin.site.register(UdlejningGrill, UdlejningGrillAdmin)
