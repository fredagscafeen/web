from django.contrib.postgres.fields import ArrayField
from django.db import models
from unfold.admin import ModelAdmin
from unfold.contrib.forms.widgets import ArrayWidget, WysiwygWidget


# Options at: https://unfoldadmin.com/docs/configuration/modeladmin/
class CustomModelAdmin(ModelAdmin):
    show_add_link = True
    compressed_fields = True
    warn_unsaved_form = True
    list_filter_submit = False
    list_fullwidth = True
    list_filter_sheet = False
    list_horizontal_scrollbar_top = False
    list_disable_select_all = False
    change_form_show_cancel_button = True

    formfield_overrides = {
        models.TextField: {
            "widget": WysiwygWidget,
        },
        ArrayField: {
            "widget": ArrayWidget,
        },
    }
