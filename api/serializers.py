from rest_framework import serializers

from bartenders.models import Bartender
from items.models import BeerType, Item, Brewery


class BrewerySerializer(serializers.ModelSerializer):
    class Meta:
        model = Brewery
        fields = '__all__'


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = '__all__'


class BartenderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bartender
        fields = ('id', 'name', 'username', 'isActiveBartender')


class BeerTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BeerType
        fields = '__all__'
