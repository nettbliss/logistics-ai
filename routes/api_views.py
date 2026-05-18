
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from .serializers import OrderSerializer, RouteSerializer, RouteHistorySerializer
from core.models import Order, RouteHistory
from .models import Route


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