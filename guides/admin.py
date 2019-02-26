from django.contrib import admin

from .models import Guide


@admin.register(Guide)
class GuideAdmin(admin.ModelAdmin):
	pass
