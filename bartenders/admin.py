from django.contrib import admin
from django.utils.safestring import mark_safe
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.db.models.expressions import Case, When, Value
from django.db import models

from django_object_actions import DjangoObjectActions

from bartenders.models import Bartender, BoardMember, BartenderApplication, BartenderShift, BoardMemberDepositShift
from fredagscafeen.admin_filters import NonNullFieldListFilter


class BartenderAdmin(admin.ModelAdmin):
    list_display = ('name', 'username', 'email')
    search_fields = ('name', 'username', 'email')
    list_filter = ('isActiveBartender', ('boardmember', NonNullFieldListFilter))


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
                    When(isActiveBartender=True, then=Value(1)),
                    default=2,
                    output_field=models.IntegerField(),
                )
            ).order_by('order', 'name')

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == 'other_bartenders':
            kwargs['queryset'] = Bartender.objects.annotate(
                order=Case(
                    When(isActiveBartender=True, then=Value(0)),
                    default=1,
                    output_field=models.IntegerField(),
                )
            ).order_by('order', 'name')

        return super().formfield_for_manytomany(db_field, request, **kwargs)


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
