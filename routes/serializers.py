from rest_framework import serializers
from .models import Route
from core.models import Order, RouteHistory, Vehicle, Cargo


class OrderSerializer(serializers.ModelSerializer):
    """
    Сериализатор для заказов.
    
    Пример создания заказа:
    {
        "order_number": "ORD-001",
        "client": 1,
        "cargo": 1,
        "vehicle": 1,
        "pickup_address": "Москва, ул. Тверская, 1",
        "delivery_address": "Санкт-Петербург, Невский пр., 50",
        "waypoints": ["Тверь, ул. Революции, 12"],
        "status": "pending"
    }
    """
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class RouteSerializer(serializers.ModelSerializer):
    """
    Сериализатор для маршрутов.
    
    Ответ содержит оптимизированный порядок точек и параметры маршрута.
    """
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    
    class Meta:
        model = Route
        fields = '__all__'
        read_only_fields = ('created_at',)


class RouteHistorySerializer(serializers.ModelSerializer):
    """
    Сериализатор для истории расчётов.
    """
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    
    class Meta:
        model = RouteHistory
        fields = '__all__'
        read_only_fields = ('created_at',)


class VehicleSerializer(serializers.ModelSerializer):
    """
    Сериализатор для транспортных средств.
    
    Пример добавления ТС:
    {
        "license_plate": "A123BC",
        "type": "truck",
        "capacity_kg": 5000,
        "fuel_consumption": 25.5,
        "is_active": true
    }
    """
    class Meta:
        model = Vehicle
        fields = '__all__'


class CargoSerializer(serializers.ModelSerializer):
    """
    Сериализатор для грузов.
    
    Пример добавления груза:
    {
        "name": "Строительные материалы",
        "weight_kg": 1500,
        "volume_m3": 4.5,
        "is_hazardous": false,
        "requires_temperature": false
    }
    """
    class Meta:
        model = Cargo
        fields = '__all__'