from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.views.generic import RedirectView

urlpatterns = [
    url(r'^favicon.ico$', RedirectView.as_view(url='/static/favicon.ico')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^api/', include('api.urls')),
    url(r'^', include('web.urls'))
]

if settings.DEBUG:
    # Handle user-uploaded content during development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
