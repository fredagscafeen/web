import datetime

from django.contrib import admin
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.safestring import mark_safe
from django_object_actions import DjangoObjectActions

from udlejning.models import Udlejning, UdlejningApplication, UdlejningGrill, UdlejningProjector, UdlejningSpeakers


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
@admin.register(Udlejning)
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
			'fields': (('whoPays', 'association'), ('paymentType', 'billSendTo', 'EANnumber'), ('expectedConsummation', 'actualConsummation'), ('invoice_number', 'total_price', 'payment_due_date'))
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
		suffix = ''
		if obj.status == 'sent' and obj.payment_due_date != None:
			diff = (obj.payment_due_date - datetime.date.today()).days
			if diff == 0:
				delta = 'i dag'
			elif diff > 0:
				if diff == 1:
					delta = 'i morgen'
				else:
					delta = f'om {diff} dage'
			else:
				if diff == -1:
					delta = 'i går!'
				else:
					delta = f'{-diff} dage siden!'

			suffix = f' ({obj.payment_due_date}, {delta})'
		return mark_safe(f'<img src="{ static(f"admin/img/icon-{icon}.svg") }"> {obj.get_status_display()}{suffix}')


@admin.register(UdlejningApplication)
class UdlejningApplicationAdmin(DjangoObjectActions, admin.ModelAdmin):
    list_display = ('dateFrom', 'whoReserved')

    change_actions = ('accept', 'deny')

    def accept(self, request, obj):
        pk = obj.accept()
        obj.delete()
        return HttpResponseRedirect(reverse('admin:udlejning_udlejning_change', args=(pk, )))

    def deny(self, request, obj):
        obj.delete()
        return HttpResponseRedirect(reverse('admin:udlejning_udlejningapplication_changelist'))


@admin.register(UdlejningGrill)
class UdlejningGrillAdmin(admin.ModelAdmin):
	ordering = ('-dateFrom',)
	list_display = ('dateFrom', 'whoReserved', 'in_charge')
	filter_horizontal = ('bartendersInCharge',)

	def get_queryset(self, request):
		qs = super().get_queryset(request)
		return qs.prefetch_related('bartendersInCharge')

	def in_charge(self, obj):
		return ', '.join(obj.bartendersInCharge.values_list('username', flat=True))


@admin.register(UdlejningProjector)
class UdlejningProjectorAdmin(admin.ModelAdmin):
	ordering = ('-dateFrom',)
	list_display = ('dateFrom', 'whoReserved')


@admin.register(UdlejningSpeakers)
class UdlejningSpeakersAdmin(admin.ModelAdmin):
	ordering = ('-dateFrom',)
	list_display = ('dateFrom', 'whoReserved')
