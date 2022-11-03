from rest_framework import serializers
from my_api.models import Menu

class MenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = Menu
        fields = ('id', 'menu', 'menuId', 'placeId', 'placeName', 'merchantId')