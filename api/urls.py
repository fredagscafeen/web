from django.conf.urls import url, include
from rest_framework import routers

from api.views import BartenderViewSet, LastModifiedView, IsBartenderView
from api.views import BeerTypeViewSet
from api.views import BreweryViewSet
from api.views import ItemViewSet
# from bartenders.views import IsUsernameBartender

router = routers.DefaultRouter()
router.register(r'items', ItemViewSet)
router.register(r'breweries', BreweryViewSet)
router.register(r'beerTypes', BeerTypeViewSet)
router.register(r'bartenders', BartenderViewSet)

urlpatterns = [
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^last-modified/', LastModifiedView.as_view(), name='last-modified'),
    url(r'^is-bartender/(?P<username>\w+)/', IsBartenderView.as_view(), name='is_bartender'),
]

urlpatterns += router.urls

