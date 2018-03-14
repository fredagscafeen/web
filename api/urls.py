from django.urls import path, include
from rest_framework import routers

from api.views import BartenderViewSet, LastModifiedView, IsBartenderView, TokenAuthView
from api.views import BeerTypeViewSet
from api.views import BreweryViewSet
from api.views import ItemViewSet

router = routers.DefaultRouter()
router.register(r'items', ItemViewSet, 'items')
router.register(r'breweries', BreweryViewSet, 'breweries')
router.register(r'beerTypes', BeerTypeViewSet)
router.register(r'bartenders', BartenderViewSet)

urlpatterns = [
	path('auth/', TokenAuthView.as_view(), name='token-auth'),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('last-modified/', LastModifiedView.as_view(), name='last-modified'),
    path('is-bartender/<username>/', IsBartenderView.as_view(), name='is_bartender'),
]

urlpatterns += router.urls
