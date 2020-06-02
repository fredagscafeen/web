from django.urls import include, path
from rest_framework import routers

from api.views import (
    BartenderViewSet,
    BeerTypeViewSet,
    BreweryViewSet,
    IsBartenderView,
    ItemViewSet,
    LastModifiedView,
    PrintStatusView,
    TokenAuthView,
)

router = routers.DefaultRouter()
router.register(r"items", ItemViewSet, "items")
router.register(r"breweries", BreweryViewSet, "breweries")
router.register(r"beerTypes", BeerTypeViewSet)
router.register(r"bartenders", BartenderViewSet)

urlpatterns = [
    path("auth/", TokenAuthView.as_view(), name="token-auth"),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    path("last-modified/", LastModifiedView.as_view(), name="last-modified"),
    path("is-bartender/<username>/", IsBartenderView.as_view(), name="is_bartender"),
    path("print_status/<job_id>/", PrintStatusView.as_view(), name="print_status"),
]

urlpatterns += router.urls
