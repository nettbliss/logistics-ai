import asyncio
from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Route
from .algorithm import optimize_route_with_real_distances, get_coordinates, haversine_distance
from core.models import Order


def index(request):
    return render(request, 'routes/index.html')


def test_page(request):
    return render(request, 'routes/test.html')


def multi_page(request):
    return render(request, 'routes/multi.html')


class RouteViewSet(viewsets.ViewSet):
    
    @action(detail=False, methods=['post'])
    def calculate(self, request):
        order_id = request.data.get('order_id')
        algorithm = request.data.get('algorithm', 'genetic')
        waypoints = request.data.get('waypoints', [])
        pickup_address = request.data.get('pickup_address', '')
        delivery_address = request.data.get('delivery_address', '')
        
        order = get_object_or_404(Order, id=order_id)
        
        if pickup_address:
            order.pickup_address = pickup_address
        if delivery_address:
            order.delivery_address = delivery_address
        if waypoints:
            order.waypoints = waypoints
        order.save()
        
        addresses = order.get_all_addresses()
        
        async def get_coordinates_for_addresses():
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
        coordinates = loop.run_until_complete(get_coordinates_for_addresses())
        loop.close()
        
        existing_route = Route.objects.filter(order=order).first()
        if existing_route:
            existing_route.delete()
        
        result = optimize_route_with_real_distances(addresses, coordinates, method=algorithm)
        
        route = Route.objects.create(
            order=order,
            vehicle=order.vehicle if order.vehicle else None,
            total_distance_km=result['total_distance_km'],
            estimated_time_min=int(result['total_distance_km'] * 1.2),
            fuel_cost=result['total_distance_km'] * 50,
            waypoints=result['optimized_order'],
            algorithm_used=result['algorithm'],
            optimization_score=round(100 - result['total_distance_km'] / 10, 2)
        )
        
        return Response({
            'status': 'success',
            'route_id': route.id,
            'total_distance': result['total_distance_km'],
            'optimized_order': result['optimized_order'],
            'algorithm': 'Genetic algorithm' if result['algorithm'] == 'genetic' else 'Branch and bound',
            'points_count': result['points_count']
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def compare(self, request):
        """Сравнение оптимизированного и обычного маршрута"""
        order_id = request.data.get('order_id')
        waypoints = request.data.get('waypoints', [])
        pickup_address = request.data.get('pickup_address', '')
        delivery_address = request.data.get('delivery_address', '')
        
        order = get_object_or_404(Order, id=order_id)
        
        if pickup_address:
            order.pickup_address = pickup_address
        if delivery_address:
            order.delivery_address = delivery_address
        if waypoints:
            order.waypoints = waypoints
        order.save()
        
        addresses = order.get_all_addresses()
        
        async def get_coordinates_for_addresses():
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
        coordinates = loop.run_until_complete(get_coordinates_for_addresses())
        loop.close()
        
        # Обычный маршрут
        naive_distance = 0
        for i in range(len(coordinates) - 1):
            naive_distance += haversine_distance(
                coordinates[i][0], coordinates[i][1],
                coordinates[i+1][0], coordinates[i+1][1]
            )
        
        # Оптимизированный маршрут
        optimized_result = optimize_route_with_real_distances(addresses, coordinates, method='genetic')
        optimized_distance = optimized_result['total_distance_km']
        
        # Экономия
        economy_km = round(naive_distance - optimized_distance, 2)
        economy_percent = round((economy_km / naive_distance) * 100, 2) if naive_distance > 0 else 0
        fuel_price_per_km = 50
        fuel_saved = round(economy_km * fuel_price_per_km, 2)
        
        return Response({
            'naive_order': addresses,
            'naive_distance': round(naive_distance, 2),
            'optimized_order': optimized_result['optimized_order'],
            'optimized_distance': optimized_result['total_distance_km'],
            'economy_km': economy_km,
            'economy_percent': economy_percent,
            'fuel_saved_rub': fuel_saved
        })