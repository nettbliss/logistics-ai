from django.contrib import admin
from .models import Route

@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'total_distance_km', 'estimated_time_min', 'algorithm_used')
    readonly_fields = ('created_at',)