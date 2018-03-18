from django.contrib import admin
from django.utils.safestring import mark_safe
from django.http import HttpResponseRedirect
from django.urls import reverse

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
    list_display = ('date', 'shift_responsible', 'other_bartenders_list')
    filter_horizontal = ('other_bartenders',)

    def shift_responsible(self, obj):
        return obj.responsible.name

    def other_bartenders_list(self, obj):
        return ", ".join([s.name for s in obj.other_bartenders.all()])


class BoardMemberDepositShiftAdmin(admin.ModelAdmin):
    list_display = ('date', 'responsible_board_members')
    filter_horizontal = ('responsibles',)

    def responsible_board_members(self, obj):
        return ", ".join([s.name for s in obj.responsibles.all()])

admin.site.register(Bartender, BartenderAdmin)
admin.site.register(BoardMember, BoardMemberAdmin)
admin.site.register(BartenderApplication, BartenderApplicationAdmin)
admin.site.register(BartenderShift, BartenderShiftAdmin)
admin.site.register(BoardMemberDepositShift, BoardMemberDepositShiftAdmin)
