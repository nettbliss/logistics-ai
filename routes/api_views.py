from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from .serializers import OrderSerializer, RouteSerializer, RouteHistorySerializer
from core.models import Order, RouteHistory
from .models import Route
import asyncio
import time


class TestAPIView(APIView):
    """Тестовый API для проверки авторизации"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            'status': 'ok',
            'message': 'Вы успешно авторизованы!',
            'user': request.user.username
        })


class OrderViewSet(viewsets.ModelViewSet):
    """API для управления заказами"""
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'client':
            return self.queryset.filter(client=user)
        return self.queryset


class RouteViewSet(viewsets.ReadOnlyModelViewSet):
    """API для просмотра маршрутов"""
    queryset = Route.objects.all()
    serializer_class = RouteSerializer
    permission_classes = [IsAuthenticated]


class RouteHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """API для истории маршрутов"""
    queryset = RouteHistory.objects.all()
    serializer_class = RouteHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        order_id = self.request.query_params.get('order_id')
        if order_id:
            return self.queryset.filter(order_id=order_id)
        return self.queryset


class OptimizeAPIView(APIView):
    """API для оптимизации маршрута"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from .algorithm import optimize_route_with_real_distances, get_coordinates, haversine_distance
        
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
        
        # Обновляем адреса в заказе
        if pickup_address:
            order.pickup_address = pickup_address
        if delivery_address:
            order.delivery_address = delivery_address
        if waypoints:
            order.waypoints = waypoints
        order.save()
        
        # Получаем все адреса
        addresses = order.get_all_addresses()
        
        # Асинхронно получаем координаты
        async def get_coords():
            coords = []
            for addr in addresses:
                try:
                    coord = await get_coordinates(addr)
                    coords.append(coord)
                except Exception:
                    coords.append((55.75, 37.62))
            return coords
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        coordinates = loop.run_until_complete(get_coords())
        loop.close()
        
        # Рассчитываем обычное расстояние (как ввели)
        naive_distance = 0
        for i in range(len(coordinates) - 1):
            naive_distance += haversine_distance(
                coordinates[i][0], coordinates[i][1],
                coordinates[i+1][0], coordinates[i+1][1]
            )
        
        start_time = time.time()
        
        # Оптимизация
        result = optimize_route_with_real_distances(addresses, coordinates)
        optimized_distance = result['total_distance_km']
        economy_percent = round((naive_distance - optimized_distance) / naive_distance * 100, 2) if naive_distance > 0 else 0
        
        calculation_time_ms = (time.time() - start_time) * 1000
        
        # Удаляем старый маршрут, если есть
        Route.objects.filter(order=order).delete()
        
        # Создаём новый маршрут
        route = Route.objects.create(
            order=order,
            vehicle=order.vehicle if order.vehicle else None,
            total_distance_km=optimized_distance,
            estimated_time_min=int(optimized_distance * 1.2),
            fuel_cost=optimized_distance * 50,
            waypoints=result['optimized_order'],
            algorithm_used=result['algorithm'],
            optimization_score=economy_percent
        )
        
        # Сохраняем в историю
        RouteHistory.objects.create(
            order=order,
            optimized_order=result['optimized_order'],
            total_distance_km=optimized_distance,
            algorithm_used=result['algorithm'],
            calculation_time_ms=round(calculation_time_ms, 2),
            economy_percent=economy_percent
        )
        
        return Response({
            'status': 'success',
            'route_id': route.id,
            'total_distance': optimized_distance,
            'optimized_order': result['optimized_order'],
            'algorithm': result['algorithm'],
            'points_count': result['points_count'],
            'economy_percent': economy_percent,
            'calculation_time_ms': round(calculation_time_ms, 2)
        }, status=201)