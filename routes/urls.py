from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views
from .api_views import TestAPIView, OrderViewSet, RouteViewSet, RouteHistoryViewSet, OptimizeAPIView, CompareAPIView

router = DefaultRouter()
router.register(r'orders', OrderViewSet)
router.register(r'routes', RouteViewSet)
router.register(r'history', RouteHistoryViewSet)

urlpatterns = [
    # Веб-интерфейс
    path('', views.index, name='index'),
    path('test/', views.test_page, name='test'),
    path('multi/', views.multi_page, name='multi'),
    
    # JWT Авторизация
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # API
    path('api/', include(router.urls)),
    path('api/test/', TestAPIView.as_view(), name='api_test'),
    path('api/optimize/', OptimizeAPIView.as_view(), name='api_optimize'),
		path('api/compare/', CompareAPIView.as_view(), name='api_compare'),
]