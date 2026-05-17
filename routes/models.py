from django.db import models
from core.models import Order, Vehicle

class Route(models.Model):
    """Маршрут перевозки"""
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='route')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    
    # Данные маршрута
    total_distance_km = models.FloatField('Общее расстояние, км')
    estimated_time_min = models.IntegerField('Расчетное время, мин')
    fuel_cost = models.DecimalField('Затраты на топливо, руб', max_digits=10, decimal_places=2)
    
    # Путевые точки (будет храниться как JSON)
    waypoints = models.JSONField('Путевые точки', default=list)
    
    # Алгоритмические параметры
    algorithm_used = models.CharField('Использованный алгоритм', max_length=50, default='genetic')
    optimization_score = models.FloatField('Оценка оптимизации', default=0.0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField('Активный', default=True)
    
    def __str__(self):
        return f"Маршрут для заказа {self.order.order_number}"