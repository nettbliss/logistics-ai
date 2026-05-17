
from django.urls import path
from . import views

urlpatterns = [
    path('download/<int:route_id>/', views.download_waybill, name='download_waybill'),
]