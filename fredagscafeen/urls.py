from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("favicon.ico", RedirectView.as_view(url="/static/favicon.ico")),
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
    path("", include("web.urls")),
]

if settings.DEBUG:
    # Handle user-uploaded content during development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
