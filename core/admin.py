from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Vehicle, Cargo, Order
from django.contrib.admin import AdminSite
from django.template.response import TemplateResponse
from django.db.models import Count
from datetime import datetime


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('id', 'license_plate', 'type_badge', 'capacity_kg', 'fuel_consumption', 'current_driver', 'is_active')
    list_display_links = ('id', 'license_plate')
    list_filter = ('type', 'is_active')
    search_fields = ('license_plate', 'current_driver__username')
    list_editable = ('is_active',)
    list_per_page = 20
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('license_plate', 'type', 'is_active')
        }),
        ('Технические характеристики', {
            'fields': ('capacity_kg', 'fuel_consumption')
        }),
        ('Назначение', {
            'fields': ('current_driver',),
            'classes': ('collapse',)
        }),
    )
    
    def type_badge(self, obj):
        colors = {'truck': '#3b82f6', 'van': '#10b981', 'refrigerator': '#06b6d4'}
        color = colors.get(obj.type, '#64748b')
        names = {'truck': 'Грузовик', 'van': 'Фургон', 'refrigerator': 'Рефрижератор'}
        return format_html('<span style="background: {}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">{}</span>', color, names.get(obj.type, obj.type))
    type_badge.short_description = 'Тип ТС'


@admin.register(Cargo)
class CargoAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'weight_kg', 'volume_m3', 'hazardous_badge', 'temp_badge')
    list_display_links = ('id', 'name')
    list_filter = ('is_hazardous', 'requires_temperature')
    search_fields = ('name',)
    list_per_page = 20
    
    def hazardous_badge(self, obj):
        if obj.is_hazardous:
            return format_html('<span style="background: #ef4444; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">Опасный</span>')
        return format_html('<span style="background: #e2e8f0; color: #475569; padding: 2px 8px; border-radius: 12px; font-size: 11px;">Обычный</span>')
    hazardous_badge.short_description = 'Класс опасности'
    
    def temp_badge(self, obj):
        if obj.requires_temperature:
            return '❄️ Требует охлаждения'
        return '—'
    temp_badge.short_description = 'Температурный режим'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'order_number', 'client_link', 'cargo', 'vehicle', 'status_badge', 'distance_info', 'created_at')
    list_display_links = ('id', 'order_number')
    list_filter = ('status', 'created_at')
    search_fields = ('order_number', 'client__username', 'client__company_name')
    list_per_page = 20
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Информация о заказе', {
            'fields': ('order_number', 'client', 'status')
        }),
        ('Груз и транспорт', {
            'fields': ('cargo', 'vehicle')
        }),
        ('Маршрут', {
            'fields': ('pickup_address', 'waypoints', 'delivery_address'),
            'description': 'Укажите адрес загрузки, промежуточные точки (каждая с новой строки) и адрес доставки'
        }),
        ('Временные параметры', {
            'fields': ('pickup_date', 'delivery_deadline'),
            'classes': ('collapse',)
        }),
    )
    
    def client_link(self, obj):
        url = reverse('admin:accounts_user_change', args=[obj.client.id])
        return format_html('<a href="{}" style="font-weight:500;">{}</a>', url, obj.client.username)
    client_link.short_description = 'Клиент'
    
    def status_badge(self, obj):
        colors = {
            'pending': '#f59e0b',
            'loading': '#3b82f6',
            'in_transit': '#8b5cf6',
            'delivered': '#10b981',
            'delayed': '#ef4444',
            'damaged': '#dc2626',
        }
        names = {
            'pending': 'Ожидает',
            'loading': 'Загружается',
            'in_transit': 'В пути',
            'delivered': 'Доставлен',
            'delayed': 'Задержан',
            'damaged': 'Повреждён',
        }
        color = colors.get(obj.status, '#64748b')
        return format_html('<span style="background: {}; color: white; padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: 500;">{}</span>', color, names.get(obj.status, obj.status))
    status_badge.short_description = 'Статус'
    
    def distance_info(self, obj):
        if hasattr(obj, 'route') and obj.route:
            return format_html('<span style="font-weight:600;">{} км</span><br><span style="font-size:10px; color:#64748b;">оптимизирован</span>', obj.route.total_distance_km)
        return '—'
    distance_info.short_description = 'Расстояние'


class LogisticsAdminSite(AdminSite):
    site_header = 'OptiRoute Логистика'
    site_title = 'OptiRoute'
    index_title = 'Панель управления'
    
    def index(self, request, extra_context=None):
        from .models import Order
        
        total_orders = Order.objects.count()
        in_transit = Order.objects.filter(status='in_transit').count()
        delivered_today = Order.objects.filter(status='delivered', updated_at__date=datetime.now().date()).count()
        delayed = Order.objects.filter(status='delayed').count()
        recent_orders = Order.objects.order_by('-created_at')[:10]
        
        context = {
            **self.each_context(request),
            'total_orders': total_orders,
            'in_transit': in_transit,
            'delivered_today': delivered_today,
            'delayed': delayed,
            'recent_orders': recent_orders,
        }
        return TemplateResponse(request, 'admin/custom_index.html', context)