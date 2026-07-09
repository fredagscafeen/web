from django.urls import path

from . import views

urlpatterns = [
    # Captures anything after /qr/ as a string and names it 'slug'
    path("<str:slug>/", views.qr_redirect_view, name="qr_redirect"),
]
