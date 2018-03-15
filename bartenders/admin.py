from django.contrib import admin
from django.utils.safestring import mark_safe
from django.http import HttpResponseRedirect
from django.urls import reverse

from django_object_actions import DjangoObjectActions

from bartenders.models import Bartender, BoardMember, BartenderApplication
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


admin.site.register(Bartender, BartenderAdmin)
admin.site.register(BoardMember, BoardMemberAdmin)
admin.site.register(BartenderApplication, BartenderApplicationAdmin)
