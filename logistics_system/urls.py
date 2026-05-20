from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Swagger/OpenAPI конфигурация
schema_view = get_schema_view(
    openapi.Info(
        title="OptiRoute API",
        default_version="v1.0",
        description="""
API для логистической платформы OptiRoute.

Основные возможности:
- Управление заказами, транспортом и грузами
- Оптимизация маршрутов с помощью генетического алгоритма
- Сравнение обычного и оптимизированного маршрута
- История расчётов

Аутентификация:
Для доступа к API требуется JWT-токен.
1. Получите токен через POST /api/token/
2. Используйте его в заголовке: Authorization: Bearer <token>

Алгоритм оптимизации:
Генетический алгоритм фиксирует первую и последнюю точки маршрута (загрузка и доставка) 
и находит оптимальный порядок промежуточных точек. Расстояния рассчитываются через Яндекс.Геокодер.
        """,
        terms_of_service="https://github.com/nettbliss/logistics-ai",
        contact=openapi.Contact(
            name="OptiRoute Support",
            email="support@optiroute.com",
            url="https://github.com/nettbliss/logistics-ai"
        ),
        license=openapi.License(
            name="MIT License",
            url="https://opensource.org/licenses/MIT"
        ),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('', include('routes.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)