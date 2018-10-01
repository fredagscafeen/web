from django.contrib import admin
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.safestring import mark_safe
from django_object_actions import DjangoObjectActions

from udlejning.models import Udlejning, UdlejningApplication, UdlejningGrill


class StatusDoneListFilter(admin.SimpleListFilter):
	title = 'betalt'
	parameter_name = 'paid'

	def lookups(self, request, model_admin):
		return (
			('notpaid', 'Ikke betalt'),
			('paid', 'Betalt'),
		)

	def queryset(self, request, queryset):
		if self.value() == 'notpaid':
			return queryset.exclude(status='paid')
		if self.value() == 'paid':
			return queryset.filter(status='paid')


# Remember to cut down to 2 classes
class UdlejningAdmin(admin.ModelAdmin):
	ordering = ('-dateFrom',)
	list_display = ('dateFrom', 'whoReserved', 'in_charge', 'draftBeerSystem', 'association', '_status')
	filter_horizontal = ('bartendersInCharge', )
	list_filter = (StatusDoneListFilter, 'status', 'association', 'draftBeerSystem')

	fieldsets = (
		(None, {
			'fields': (('dateFrom', 'dateTo', 'where'),)
		}),
		('Lejer', {
			'fields': (('whoReserved', 'contactEmail', 'contactPhone'),)
		}),
		('Betaling', {
			'fields': (('whoPays', 'association'), ('paymentType', 'billSendTo', 'EANnumber'), ('expectedConsummation', 'actualConsummation'))
		}),
		('Internt', {
			'fields': (('draftBeerSystem', 'status'), 'bartendersInCharge', 'comments')
		})
	)

	def get_queryset(self, request):
		qs = super().get_queryset(request)
		return qs.prefetch_related('bartendersInCharge')

	def in_charge(self, obj):
		return ', '.join(obj.bartendersInCharge.values_list('username', flat=True))

	def _status(self, obj):
		icon = {'notsent': 'no', 'sent': 'unknown', 'paid': 'yes'}.get(obj.status, 'unknown')
		return mark_safe(f'<img src="{ static(f"admin/img/icon-{icon}.svg") }"> {obj.get_status_display()}')


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
