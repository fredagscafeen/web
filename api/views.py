from rest_framework import viewsets, parsers, renderers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.permissions import IsAuthenticatedOrReadOnly, DjangoModelPermissionsOrAnonReadOnly
from rest_framework.authentication import SessionAuthentication, BasicAuthentication, TokenAuthentication

from django.contrib.auth.models import Permission

from api.serializers import BartenderSerializer
from api.serializers import BeerTypeSerializer
from api.serializers import BrewerySerializer
from api.serializers import ItemSerializer
from bartenders.models import Bartender
from items.models import BeerType
from items.models import Brewery
from items.models import Item

class ItemViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticatedOrReadOnly, DjangoModelPermissionsOrAnonReadOnly,)
    authentication_classes = (BasicAuthentication, SessionAuthentication, TokenAuthentication,)
    
    queryset = Item.objects.all()
    serializer_class = ItemSerializer


class BreweryViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticatedOrReadOnly, DjangoModelPermissionsOrAnonReadOnly,)
    authentication_classes = (BasicAuthentication, SessionAuthentication, TokenAuthentication,)
    
    queryset = Brewery.objects.all()
    serializer_class = BrewerySerializer


class BeerTypeViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticatedOrReadOnly, DjangoModelPermissionsOrAnonReadOnly,)
    authentication_classes = (BasicAuthentication, SessionAuthentication, TokenAuthentication,)
    
    queryset = BeerType.objects.all()
    serializer_class = BeerTypeSerializer


class BartenderViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticatedOrReadOnly, DjangoModelPermissionsOrAnonReadOnly,)
    authentication_classes = (BasicAuthentication, SessionAuthentication, TokenAuthentication,)
    
    queryset = Bartender.objects.all()
    serializer_class = BartenderSerializer


class LastModifiedView(APIView):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    authentication_classes = (BasicAuthentication, SessionAuthentication, TokenAuthentication,)

    def get(self, request, format=None):
        last_modified = None
        for item in Item.objects.all():
            if item.lastModified > last_modified or last_modified is None:
                last_modified = item.lastModified
        return Response(last_modified, status=status.HTTP_200_OK)


class IsBartenderView(APIView):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    authentication_classes = (BasicAuthentication, SessionAuthentication, TokenAuthentication,)

    def get(self, request, username, format=None):
        is_bartender = False
        try:
            if Bartender.objects.get(username=username).isActiveBartender:
                is_bartender = True
        except Bartender.DoesNotExist:
            pass
        return Response(is_bartender, status=status.HTTP_200_OK)


class TokenAuthView(APIView):
    throttle_classes = ()
    permission_classes = ()
    parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.JSONParser,)
    renderer_classes = (renderers.JSONRenderer,)
    serializer_class = AuthTokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'permissions': user.get_all_permissions()})