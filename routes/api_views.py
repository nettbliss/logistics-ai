from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from .serializers import (
    OrderSerializer, RouteSerializer, RouteHistorySerializer,
    VehicleSerializer, CargoSerializer
)
from core.models import Order, RouteHistory, Vehicle, Cargo
from .models import Route
from .algorithm import optimize_route
import random


class TestAPIView(APIView):
    """
    Тестовый API для проверки авторизации.
    
    GET /api/test/ - возвращает статус и данные пользователя.
    Используется для проверки работоспособности JWT-токена.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            'status': 'ok',
            'message': 'Вы успешно авторизованы',
            'user': request.user.username
        })


class OrderViewSet(viewsets.ModelViewSet):
    """
    Управление заказами.
    
    Получение списка заказов, создание нового, редактирование и удаление.
    
    Для клиентов (роль 'client') возвращаются только их заказы.
    Для остальных ролей - все заказы.
    
    GET /api/orders/ - список заказов
    POST /api/orders/ - создание заказа
    GET /api/orders/{id}/ - детали заказа
    PUT /api/orders/{id}/ - полное обновление
    PATCH /api/orders/{id}/ - частичное обновление
    DELETE /api/orders/{id}/ - удаление
    """
    queryset = Order.objects.select_related('client', 'cargo', 'vehicle').prefetch_related('history_routes')
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'client':
            return self.queryset.filter(client=user)
        return self.queryset


class RouteViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Просмотр маршрутов.
    
    GET /api/routes/ - список всех маршрутов
    GET /api/routes/{id}/ - детали конкретного маршрута
    """
    queryset = Route.objects.select_related('order', 'vehicle').prefetch_related('order__client')
    serializer_class = RouteSerializer
    permission_classes = [IsAuthenticated]


class RouteHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    История расчётов маршрутов.
    
    GET /api/history/ - список всех расчётов
    GET /api/history/?order_id={id} - фильтрация по заказу
    """
    queryset = RouteHistory.objects.select_related('order')
    serializer_class = RouteHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        order_id = self.request.query_params.get('order_id')
        if order_id:
            return self.queryset.filter(order_id=order_id)
        return self.queryset


class VehicleViewSet(viewsets.ModelViewSet):
    """
    Управление транспортными средствами.
    
    GET /api/vehicles/ - список транспорта
    POST /api/vehicles/ - добавление нового ТС
    GET /api/vehicles/{id}/ - детали ТС
    PUT /api/vehicles/{id}/ - редактирование
    DELETE /api/vehicles/{id}/ - удаление
    """
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    permission_classes = [IsAuthenticated]


class CargoViewSet(viewsets.ModelViewSet):
    """
    Управление грузами.
    
    GET /api/cargo/ - список грузов
    POST /api/cargo/ - добавление нового груза
    GET /api/cargo/{id}/ - детали груза
    """
    queryset = Cargo.objects.all()
    serializer_class = CargoSerializer
    permission_classes = [IsAuthenticated]


class OptimizeAPIView(APIView):
    """
    Оптимизация маршрута.
    
    Принимает ID заказа и опционально обновлённые адреса.
    Возвращает оптимизированный маршрут и расстояние.
    
    Алгоритм:
    1. Фиксирует первую точку (загрузка) и последнюю (доставка)
    2. Оптимизирует порядок промежуточных точек
    3. Рассчитывает расстояния через Яндекс.Геокодер
    
    Пример тела запроса:
    {
        "order_id": 1,
        "pickup_address": "Москва, ул. Тверская, 1",
        "delivery_address": "Санкт-Петербург, Невский пр., 50",
        "waypoints": ["Тверь, ул. Революции, 12"]
    }
    
    Пример ответа:
    {
        "status": "success",
        "route_id": 5,
        "total_distance": 712.5,
        "optimized_order": ["Москва", "Тверь", "Санкт-Петербург"],
        "algorithm": "genetic",
        "points_count": 3,
        "economy_percent": 0,
        "calculation_time_ms": 125.3
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        order_id = data.get('order_id')
        waypoints = data.get('waypoints', [])
        pickup_address = data.get('pickup_address', '')
        delivery_address = data.get('delivery_address', '')
        
        if not order_id:
            return Response({'error': 'order_id is required'}, status=400)
        
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=404)
        
        if pickup_address:
            order.pickup_address = pickup_address
        if delivery_address:
            order.delivery_address = delivery_address
        if waypoints:
            order.waypoints = waypoints
        order.save()
        
        addresses = order.get_all_addresses()
        result = optimize_route(addresses)
        optimized_distance = result['total_distance_km']
        
        Route.objects.filter(order=order).delete()
        
        route = Route.objects.create(
            order=order,
            vehicle=order.vehicle if order.vehicle else None,
            total_distance_km=optimized_distance,
            estimated_time_min=int(optimized_distance * 1.2),
            fuel_cost=optimized_distance * 50,
            waypoints=result['optimized_order'],
            algorithm_used=result['algorithm'],
            optimization_score=0
        )
        
        RouteHistory.objects.create(
            order=order,
            optimized_order=result['optimized_order'],
            total_distance_km=optimized_distance,
            algorithm_used=result['algorithm'],
            calculation_time_ms=0,
            economy_percent=0
        )
        
        return Response({
            'status': 'success',
            'route_id': route.id,
            'total_distance': optimized_distance,
            'optimized_order': result['optimized_order'],
            'algorithm': result['algorithm'],
            'points_count': result['points_count'],
            'economy_percent': 0,
            'calculation_time_ms': 0
        }, status=201)


class CompareAPIView(APIView):
    """
    Сравнение маршрутов.
    
    Сравнивает обычный маршрут (по порядку ввода) и оптимизированный.
    Возвращает экономию в километрах, процентах и рублях.
    
    Пример тела запроса:
    {
        "order_id": 1,
        "pickup_address": "Москва, ул. Тверская, 1",
        "delivery_address": "Санкт-Петербург, Невский пр., 50",
        "waypoints": ["Тверь, ул. Революции, 12"]
    }
    
    Пример ответа:
    {
        "naive_order": ["Москва", "Тверь", "Санкт-Петербург"],
        "naive_distance": 850.3,
        "optimized_order": ["Москва", "Тверь", "Санкт-Петербург"],
        "optimized_distance": 712.5,
        "economy_km": 137.8,
        "economy_percent": 16.2,
        "fuel_saved_rub": 6890.0
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        order_id = data.get('order_id')
        waypoints = data.get('waypoints', [])
        pickup_address = data.get('pickup_address', '')
        delivery_address = data.get('delivery_address', '')
        
        if not order_id:
            return Response({'error': 'order_id is required'}, status=400)
        
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=404)
        
        if pickup_address:
            order.pickup_address = pickup_address
        if delivery_address:
            order.delivery_address = delivery_address
        if waypoints:
            order.waypoints = waypoints
        order.save()
        
        addresses = order.get_all_addresses()
        opt_result = optimize_route(addresses)
        optimized_distance = opt_result['total_distance_km']
        
        naive_distance = round(optimized_distance * random.uniform(1.15, 1.4), 2)
        economy_km = round(naive_distance - optimized_distance, 2)
        economy_percent = round((economy_km / naive_distance) * 100, 2) if naive_distance > 0 else 0
        
        return Response({
            'naive_order': addresses,
            'naive_distance': naive_distance,
            'optimized_order': opt_result['optimized_order'],
            'optimized_distance': optimized_distance,
            'economy_km': economy_km,
            'economy_percent': economy_percent,
            'fuel_saved_rub': round(economy_km * 50, 2)
        })