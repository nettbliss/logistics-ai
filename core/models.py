from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Vehicle(models.Model):
    """Транспортное средство"""
    VEHICLE_TYPES = [
        ('truck', 'Грузовик'),
        ('van', 'Фургон'),
        ('refrigerator', 'Рефрижератор'),
    ]
    
    license_plate = models.CharField('Госномер', max_length=20, unique=True)
    type = models.CharField('Тип ТС', max_length=20, choices=VEHICLE_TYPES)
    capacity_kg = models.FloatField('Грузоподъемность, кг')
    fuel_consumption = models.FloatField('Расход топлива, л/100км')
    current_driver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={'role': 'driver'})
    is_active = models.BooleanField('В эксплуатации', default=True)
    
    def __str__(self):
        return f"{self.license_plate} ({self.get_type_display()})"


class Cargo(models.Model):
    """Груз"""
    name = models.CharField('Наименование', max_length=200)
    weight_kg = models.FloatField('Вес, кг')
    volume_m3 = models.FloatField('Объем, м³')
    is_hazardous = models.BooleanField('Опасный груз', default=False)
    requires_temperature = models.BooleanField('Требует температурный режим', default=False)
    
    def __str__(self):
        return self.name


class Order(models.Model):
    """Заказ на перевозку"""
    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('loading', 'Загружается'),
        ('in_transit', 'В пути'),
        ('delivered', 'Доставлен'),
        ('delayed', 'Задержан'),
        ('damaged', 'Поврежден'),
    ]
    
    order_number = models.CharField('Номер заказа', max_length=50, unique=True)
    client = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'client'}, related_name='orders')
    cargo = models.ForeignKey(Cargo, on_delete=models.CASCADE)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True)
    
    pickup_address = models.TextField('Адрес загрузки')
    delivery_address = models.TextField('Адрес доставки')
    waypoints = models.JSONField('Промежуточные точки', default=list, blank=True)
    
    pickup_date = models.DateTimeField('Дата и время загрузки', null=True, blank=True)
    delivery_deadline = models.DateTimeField('Крайний срок доставки', null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def get_all_addresses(self):
        addresses = [self.pickup_address]
        if self.waypoints:
            addresses.extend(self.waypoints)
        addresses.append(self.delivery_address)
        return addresses
    
    def __str__(self):
        return f"Заказ {self.order_number} - {self.client.username}"
    
    class Meta:
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['client', 'status']),
            models.Index(fields=['created_at']),
        ]


class RouteHistory(models.Model):
    """История рассчитанных маршрутов для аналитики и обучения"""
    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='history_routes')
    optimized_order = models.JSONField('Оптимальный порядок', default=list)
    total_distance_km = models.FloatField('Расстояние, км')
    algorithm_used = models.CharField('Алгоритм', max_length=50, default='genetic')
    calculation_time_ms = models.FloatField('Время расчета, мс', default=0.0)
    economy_percent = models.FloatField('Экономия, %', default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'История маршрута'
        verbose_name_plural = 'Истории маршрутов'
        indexes = [
            models.Index(fields=['order', 'created_at']),
            models.Index(fields=['algorithm_used']),
        ]
    
    def __str__(self):
        return f"История для {self.order.order_number} от {self.created_at.strftime('%d.%m.%Y')}"