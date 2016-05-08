from django.contrib import admin

# Register your models here.
from bartenders.models import Bartender, BoardMember

admin.site.register(Bartender)
admin.site.register(BoardMember)
