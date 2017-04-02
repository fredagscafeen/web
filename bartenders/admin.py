from django.contrib import admin
from django.utils.safestring import mark_safe

from bartenders.models import Bartender, BoardMember


class BartenderAdmin(admin.ModelAdmin):
    list_display = ('name', 'username', 'email')


class BoardMemberAdmin(admin.ModelAdmin):
    list_display = ('thumbnail', 'bartender', 'title')
    list_display_links = ('thumbnail', 'bartender')
    list_select_related = ('bartender', )

    def thumbnail(self, obj):
        return mark_safe('<img src="%s" width="75px"/>' % obj.image.url) if obj.image else '<missing>'

admin.site.register(Bartender, BartenderAdmin)
admin.site.register(BoardMember, BoardMemberAdmin)
