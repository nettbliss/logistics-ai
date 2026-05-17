from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('routes', views.RouteViewSet, basename='route')

urlpatterns = [
    path('', views.index, name='index'),
    path('test/', views.test_page, name='test'),
    path('multi/', views.multi_page, name='multi'),
    path('api/', include(router.urls)),
]