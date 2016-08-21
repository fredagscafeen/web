from udlejning.models import Udlejning
from udlejning.models import UdlejningGrill
from django.contrib import admin


class UdlejningAdmin(admin.ModelAdmin):
    list_display = ('dateFrom', 'whoReserved', 'boardMemberInCharge')


class UdlejningGrillAdmin(admin.ModelAdmin):
    list_display = ('dateFrom', 'whoReserved', 'boardMemberInCharge')


admin.site.register(Udlejning, UdlejningAdmin)
admin.site.register(UdlejningGrill, UdlejningGrillAdmin)
