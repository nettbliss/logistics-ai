from django.shortcuts import render, get_object_or_404, redirect
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Route
from .algorithm import optimize_route, get_coordinates, haversine_distance
from core.models import Order
import asyncio


def index(request):
    return render(request, 'routes/index.html')


def test_page(request):
    return render(request, 'routes/test.html')


def multi_page(request):
    return render(request, 'routes/multi.html')


def data_page(request):
    if not request.user.is_authenticated:
        return redirect('/admin/login/?next=/data/')
    return render(request, 'routes/data.html')


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
        
        naive_distance = 0
        for i in range(len(coordinates) - 1):
            naive_distance += haversine_distance(
                coordinates[i][0], coordinates[i][1],
                coordinates[i+1][0], coordinates[i+1][1]
            )
        
        result = optimize_route(addresses)
        optimized_distance = result['total_distance_km']
        
        existing_route = Route.objects.filter(order=order).first()
        if existing_route:
            existing_route.delete()
        
        route = Route.objects.create(
            order=order,
            vehicle=order.vehicle if order.vehicle else None,
            total_distance_km=result['total_distance_km'],
            estimated_time_min=int(result['total_distance_km'] * 1.2),
            fuel_cost=result['total_distance_km'] * 50,
            waypoints=result['optimized_order'],
            algorithm_used=result['algorithm'],
            optimization_score=round((naive_distance - optimized_distance) / naive_distance * 100, 2) if naive_distance > 0 else 0
        )
        
        return Response({
            'status': 'success',
            'route_id': route.id,
            'total_distance': result['total_distance_km'],
            'optimized_order': result['optimized_order'],
            'algorithm': 'Genetic algorithm' if result['algorithm'] == 'genetic' else 'Branch and bound',
            'points_count': result['points_count']
        }, status=status.HTTP_201_CREATED)