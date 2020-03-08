from api.serializers import (
    BartenderSerializer,
    BeerTypeSerializer,
    BrewerySerializer,
    ItemSerializer,
)
from bartenders.models import Bartender
from items.models import BeerType, Brewery, Item
from printer.models import Printer
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView


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
    permission_classes = ()

    def get(self, request, format=None):
        last_modified = None
        for item in Item.objects.all():
            if last_modified is None or item.lastModified > last_modified:
                last_modified = item.lastModified
        return Response(last_modified, status=status.HTTP_200_OK)


class IsBartenderView(APIView):
    permission_classes = ()

    def get(self, request, username, format=None):
        is_bartender = False
        try:
            if Bartender.objects.get(username=username).isActiveBartender:
                is_bartender = True
        except Bartender.DoesNotExist:
            pass
        return Response(is_bartender, status=status.HTTP_200_OK)


class TokenAuthView(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, created = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "permissions": user.get_all_permissions()})


class PrintStatusView(APIView):
    permission_classes = (IsAdminUser,)

    def get(self, request, job_id):
        status, code = Printer.get_status(job_id)
        return Response({"status": status, "code": code})
