from udlejning.models import Udlejning
from django.contrib import admin


class UdlejningAdmin(admin.ModelAdmin):
    list_display = ('dateFrom', 'whoReserved', 'boardMemberInCharge')

admin.site.register(Udlejning, UdlejningAdmin)
