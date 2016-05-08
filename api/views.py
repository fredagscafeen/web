from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from api.serializers import BartenderSerializer
from api.serializers import BeerTypeSerializer
from api.serializers import BrewerySerializer
from api.serializers import ItemSerializer
from bartenders.models import Bartender
from items.models import BeerType
from items.models import Brewery
from items.models import Item


class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer


class BreweryViewSet(viewsets.ModelViewSet):
    queryset = Brewery.objects.all()
    serializer_class = BrewerySerializer


class BeerTypeViewSet(viewsets.ModelViewSet):
    queryset = BeerType.objects.all()
    serializer_class = BeerTypeSerializer


class BartenderViewSet(viewsets.ModelViewSet):
    queryset = Bartender.objects.all()
    serializer_class = BartenderSerializer

class LastModifiedView(APIView):
    def get(self, request, format=None):
        last_modified = None
        for item in Item.objects.all():
            if item.lastModified > last_modified or last_modified is None:
                last_modified = item.lastModified
        return Response(last_modified, status=status.HTTP_200_OK)

class IsBartenderView(APIView):
    def get(self, request, username, format=None):
        is_bartender = False
        try:
            if Bartender.objects.get(username=username).isActiveBartender:
                is_bartender = True
        except Bartender.DoesNotExist:
            pass
        return Response(is_bartender, status=status.HTTP_200_OK)
