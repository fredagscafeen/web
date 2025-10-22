from django import forms
from django.contrib import admin
from django.core.exceptions import FieldError
from django.utils.safestring import mark_safe

from fredagscafeen.admin_view import custom_admin_view
from items.models import BeerType, Brewery, InventoryEntry, InventorySnapshot, Item
from printer.views import pdf_preview


def filter_by_amount(qs, positive):
    # Slow and hacky solution
    l = []

    for item in qs.all():
        if positive == (item.current_amount > 0):
            l.append(item.id)

    return qs.filter(id__in=l)


class AmountFilter(admin.SimpleListFilter):
    title = "Amount"
    parameter_name = "amount"

    def lookups(self, request, model_admin):
        return [("pos", "> 0"), ("zero", "= 0")]

    def queryset(self, request, queryset):
        value = self.value()
        if value not in ["pos", "zero"]:
            return queryset

        return filter_by_amount(queryset, value == "pos")


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("brewery", "name", "current_amount", "thumbnail")
    search_fields = ("brewery__name", "name")
    list_display_links = ("name", "thumbnail")
    list_filter = (
        AmountFilter,
        "container",
        "type",
        "brewery",
    )
    empty_value_display = ""
    ordering = ("name",)

    ordered_related_fields_to_model = {
        "brewery": Brewery,
        "type": BeerType,
    }

    def thumbnail(self, obj):
        return (
            mark_safe('<img src="%s" width="75px"/>' % obj.image.url)
            if obj.image
            else "<missing>"
        )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Makes querysets for brewery and type fields ordered by name"""
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

        try:
            model = self.ordered_related_fields_to_model[db_field.name]
            kwargs["queryset"] = model.objects.order_by("name")
        except FieldError:
            pass

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(BeerType)
class BeerTypeAdmin(admin.ModelAdmin):
    list_display = ("name",)
    ordering = ("name",)


@admin.register(Brewery)
class BreweryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    ordering = ("name",)


class InventoryEntryInlineFormSet(forms.models.BaseInlineFormSet):
    model = InventoryEntry

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.id:
            self.initial = []
            for item in filter_by_amount(Item.objects.all(), True):
                self.initial.append(
                    {
                        "amount": item.current_amount,
                        "item": item.id,
                    }
                )

            self.initial.sort(key=lambda x: -x["amount"])

    def save(self):
        super().save()


class InventoryEntryInline(admin.TabularInline):
    model = InventoryEntry
    formset = InventoryEntryInlineFormSet
    fields = ("amount", "item")
    autocomplete_fields = ["item"]

    def get_extra(self, request, obj=None, **kwargs):
        if obj:
            return super().get_extra(request, obj, **kwargs)

        return filter_by_amount(Item.objects.all(), True).count() + 1


@admin.register(InventorySnapshot)
class InventoryAdmin(admin.ModelAdmin):
    change_form_template = "admin/enhancedinline.html"
    list_display = ("datetime", "changed_items")
    inlines = [InventoryEntryInline]

    def changed_items(self, obj):
        return obj.entries.count()


class BarMenuContext:
    file_name = "barmenu"
    file_path = "barmenu/barmenu.tex"

    @staticmethod
    def get_context():
        items = Item.objects.all()
        return {
            "items": items,
        }


@custom_admin_view("items", "generate barmenu")
def generate_bartab(admin, request):
    return pdf_preview(request, admin.admin_site, BarMenuContext)
