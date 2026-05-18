from rest_framework import serializers
from .models import Route
from core.models import Order, RouteHistory


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class RouteSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    
    class Meta:
        model = Route
        fields = '__all__'
        read_only_fields = ('created_at',)


class RouteHistorySerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    
    class Meta:
        model = RouteHistory
        fields = '__all__'
        read_only_fields = ('created_at',)