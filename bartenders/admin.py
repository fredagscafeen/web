from django.conf import settings
from django.contrib import admin, messages
from django.utils.safestring import mark_safe
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.db.models.expressions import Case, When, Value
from django.db import models

from django_object_actions import DjangoObjectActions

from bartenders.models import Bartender, BoardMember, BartenderApplication, BartenderShift, BoardMemberDepositShift
from fredagscafeen.admin_filters import NonNullFieldListFilter

from .mailman2 import MailmanError


class BartenderAdmin(DjangoObjectActions, admin.ModelAdmin):
    list_display = ('name', 'username', 'email')
    search_fields = ('name', 'username', 'email')
    list_filter = ('isActiveBartender', ('boardmember', NonNullFieldListFilter))

    change_actions = ('add_to_mailing_list', 'remove_from_mailing_list')

    def add_to_mailing_list(self, request, obj):
        if not settings.MAILMAN_MUTABLE:
            messages.error(request, 'MAILMAN_MUTABLE is false!')
            return

        try:
            obj.add_to_mailing_list()
            messages.info(request, 'Successfully added to mailing list')
        except MailmanError as e:
            messages.error(request, f'Got Mailman error: {e}')

    add_to_mailing_list.label = 'Add to mailing list'

    def remove_from_mailing_list(self, request, obj):
        if not settings.MAILMAN_MUTABLE:
            messages.error(request, 'MAILMAN_MUTABLE is false!')
            return

        try:
            obj.remove_from_mailing_list()
            messages.info(request, 'Successfully removed from mailing list')
        except MailmanError as e:
            messages.error(request, f'Got Mailman error: {e}')


    remove_from_mailing_list.label = 'Remove from mailing list'


class BoardMemberAdmin(admin.ModelAdmin):
    list_display = ('thumbnail', 'bartender', 'title')
    list_display_links = ('thumbnail', 'bartender')
    list_select_related = ('bartender', )

    def thumbnail(self, obj):
        return mark_safe('<img src="%s" width="75px"/>' % obj.image.url) if obj.image else '<missing>'

class BartenderApplicationAdmin(DjangoObjectActions, admin.ModelAdmin):
    list_display = ('name', 'created', 'username', 'email')

    change_actions = ('accept', 'deny')

    def accept(self, request, obj):
        pk = obj.accept()
        obj.delete()
        return HttpResponseRedirect(reverse('admin:bartenders_bartender_change', args=(pk, )))

    def deny(self, request, obj):
        obj.delete()
        return HttpResponseRedirect(reverse('admin:bartenders_bartenderapplication_changelist'))

class BartenderShiftAdmin(admin.ModelAdmin):
    list_display = ('start_datetime', 'shift_responsible', 'other_bartenders_list')
    filter_horizontal = ('other_bartenders',)

    def shift_responsible(self, obj):
        return obj.responsible.name

    def other_bartenders_list(self, obj):
        return ", ".join([s.name for s in obj.other_bartenders.all()])

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'responsible':
            kwargs['queryset'] = Bartender.objects.annotate(
                order=Case(
                    When(boardmember__isnull=False, then=Value(0)),
                    default=1,
                    output_field=models.IntegerField(),
                )
            ).order_by('order', '-isActiveBartender', 'name')

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class BoardMemberDepositShiftAdmin(admin.ModelAdmin):
    list_display = ('start_date', 'end_date', 'responsible_board_members')
    filter_horizontal = ('responsibles',)

    def responsible_board_members(self, obj):
        return ", ".join([s.name for s in obj.responsibles.all()])

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == 'responsibles':
            kwargs['queryset'] = Bartender.objects.annotate(
                order=Case(
                    When(boardmember__isnull=False, then=Value(0)),
                    When(isActiveBartender=True, then=Value(1)),
                    default=2,
                    output_field=models.IntegerField(),
                )
            ).order_by('order', 'name')

        return super().formfield_for_manytomany(db_field, request, **kwargs)


admin.site.register(Bartender, BartenderAdmin)
admin.site.register(BoardMember, BoardMemberAdmin)
admin.site.register(BartenderApplication, BartenderApplicationAdmin)
admin.site.register(BartenderShift, BartenderShiftAdmin)
admin.site.register(BoardMemberDepositShift, BoardMemberDepositShiftAdmin)
