from django.contrib import admin

from bartenders.models import Bartender, BoardMember


class BartenderAdmin(admin.ModelAdmin):
    list_display = ('name', 'username', 'email')


class BoardMemberAdmin(admin.ModelAdmin):
    list_display = ('bartender', 'title')


admin.site.register(Bartender, BartenderAdmin)
admin.site.register(BoardMember, BoardMemberAdmin)
