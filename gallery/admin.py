from django import forms
from django.contrib import admin
from django.db import models
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from gallery.models import Album, BaseMedia


class InlineBaseMediaAdmin(admin.TabularInline):
    model = BaseMedia
    extra = 0
    fields = (
        "admin_thumbnail",
        "date",
        "caption",
        "visibility",
        "slug",
        "forcedOrder",
    )
    readonly_fields = (
        "admin_thumbnail",
        "slug",
    )

    def has_add_permission(self, request, obj=None):
        return False


class AlbumAdminForm(forms.ModelForm):
    class Meta:
        model = Album
        fields = [
            "title",
            "publish_date",
            "year",
            "thumbnail",
            "eventalbum",
            "description",
            "slug",
        ]


class AlbumAdmin(admin.ModelAdmin):
    # List display of multiple albums
    list_display = ("title", "year", "publish_date", "get_visibility_link")
    ordering = [
        "-year",
        "eventalbum",
        "-oldFolder",
        "-publish_date",
    ]  # Reverse of models.Album.ordering
    list_filter = ("year", "eventalbum")

    # Form display of single album
    inlines = [InlineBaseMediaAdmin]
    form = AlbumAdminForm
    prepopulated_fields = {
        "slug": ("title",),
    }
    formfield_overrides = {
        models.SlugField: {"widget": forms.TextInput(attrs={"readOnly": "True"})}
    }

    add_form_template = "admin/gallery/add_form.html"

    def get_inline_instances(self, request, obj=None):
        if obj is None:
            # When creating Album, don't display the BaseMedia inlines
            return []
        return super(AlbumAdmin, self).get_inline_instances(request, obj)

    def get_visibility_link(self, album):
        file = album.basemedia.first()
        if file:
            kwargs = dict(year=album.year, album_slug=album.slug, image_slug=file.slug)
            html_string = '<a href="{}?v=1">' + _("Udvælg billeder") + "</a>"
            return format_html(html_string, reverse("image", kwargs=kwargs))

    get_visibility_link.short_description = _("Udvælg billeder")

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)


admin.site.register(Album, AlbumAdmin)
