from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views
from .api_views import TestAPIView

urlpatterns = [
    # Веб-интерфейс
    path('', views.index, name='index'),
    path('test/', views.test_page, name='test'),
    path('multi/', views.multi_page, name='multi'),
    
    # JWT Авторизация
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
		
    # Тестовый API
    path('api/test/', TestAPIView.as_view(), name='api_test'),
]
