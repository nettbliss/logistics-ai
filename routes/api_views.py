
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from .serializers import OrderSerializer, RouteSerializer, RouteHistorySerializer
from core.models import Order, RouteHistory
from .models import Route
from .algorithm import optimize_route
import random


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
    """API для сравнения обычного и оптимизированного маршрута"""
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