from udlejning.models import Udlejning, UdlejningApplication, UdlejningGrill
from django.contrib import admin
from django.urls import reverse
from django.http import HttpResponseRedirect

from django_object_actions import DjangoObjectActions


# Remember to cut down to 2 classes
class UdlejningAdmin(admin.ModelAdmin):
	ordering = ('-dateFrom',)
	list_display = ('dateFrom', 'whoReserved', 'in_charge', 'draftBeerSystem', 'association', 'status')
	filter_horizontal = ('bartendersInCharge', )
	list_filter = ('status', 'association', 'draftBeerSystem')

	def get_queryset(self, request):
		qs = super().get_queryset(request)
		return qs.prefetch_related('bartendersInCharge')

	def in_charge(self, obj):
		return ', '.join(obj.bartendersInCharge.values_list('username', flat=True))


class UdlejningApplicationAdmin(DjangoObjectActions, admin.ModelAdmin):
    list_display = ('dateFrom', 'whoReserved', 'draftBeerSystem')

    change_actions = ('accept', 'deny')

    def accept(self, request, obj):
        pk = obj.accept()
        obj.delete()
        return HttpResponseRedirect(reverse('admin:udlejning_udlejning_change', args=(pk, )))

    def deny(self, request, obj):
        obj.delete()
        return HttpResponseRedirect(reverse('admin:udlejning_udlejningapplication_changelist'))


class UdlejningGrillAdmin(admin.ModelAdmin):
	ordering = ('-dateFrom',)
	list_display = ('dateFrom', 'whoReserved', 'in_charge')
	filter_horizontal = ('bartendersInCharge',)

	def get_queryset(self, request):
		qs = super().get_queryset(request)
		return qs.prefetch_related('bartendersInCharge')

	def in_charge(self, obj):
		return ', '.join(obj.bartendersInCharge.values_list('username', flat=True))


admin.site.register(Udlejning, UdlejningAdmin)
admin.site.register(UdlejningApplication, UdlejningApplicationAdmin)
admin.site.register(UdlejningGrill, UdlejningGrillAdmin)
