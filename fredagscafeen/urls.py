from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.utils.translation import gettext_lazy as _
from django.views.generic import RedirectView


def _deep_copy_obj(obj):
    """Duplicate an object and all its reverse FK / M2M relations."""
    # Snapshot M2M relations before resetting the PK.
    m2m_data = {}
    for m2m in obj._meta.many_to_many:
        m2m_data[m2m.name] = list(getattr(obj, m2m.name).all())

    # Snapshot reverse FK (one-to-many) children.
    children = []
    for related in obj._meta.related_objects:
        if related.one_to_many:
            accessor = related.get_accessor_name()
            child_qs = list(getattr(obj, accessor).all())
            children.append((related.field.name, child_qs))

    # Duplicate the object itself.
    obj.pk = None
    obj.save()

    # Restore M2M links on the new object.
    for name, items in m2m_data.items():
        getattr(obj, name).set(items)

    # Deep-copy each child, pointing it at the new parent.
    for fk_field_name, child_qs in children:
        for child in child_qs:
            setattr(child, fk_field_name, obj)
            _deep_copy_obj(child)


def duplicate_selected(modeladmin, request, queryset):
    for obj in queryset:
        _deep_copy_obj(obj)


duplicate_selected.short_description = _("Duplicate selected items")
admin.site.add_action(duplicate_selected, "duplicate_selected")

urlpatterns = i18n_patterns(
    path("favicon.ico", RedirectView.as_view(url="/static/favicon.ico")),
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
    path("", include("web.urls")),
    path("rosetta/", include("rosetta.urls")),
)

if settings.DEBUG:
    # Handle user-uploaded content during development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
