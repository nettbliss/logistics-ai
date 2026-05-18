import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from accounts.models import User
from core.models import Order, Cargo, Vehicle


@pytest.mark.django_db
class TestAPI:
    
    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            role='client'
        )
        self.cargo = Cargo.objects.create(name='Test Cargo', weight_kg=100, volume_m3=1)
        self.vehicle = Vehicle.objects.create(
            license_plate='TEST001',
            type='truck',
            capacity_kg=1000,
            fuel_consumption=20
        )
        self.order = Order.objects.create(
            order_number='TEST-001',
            client=self.user,
            cargo=self.cargo,
            vehicle=self.vehicle,
            pickup_address='Москва, ул. Тестовая, 1',
            delivery_address='Москва, ул. Проверочная, 2'
        )
    
    def test_token_obtain(self):
        url = reverse('token_obtain_pair')
        response = self.client.post(url, {
            'username': 'testuser',
            'password': 'testpass123'
        })
        assert response.status_code == 200
        assert 'access' in response.data
        assert 'refresh' in response.data
    
    def test_optimize_route_unauthorized(self):
        url = reverse('api_optimize')
        response = self.client.post(url, {'order_id': self.order.id})
        assert response.status_code == 401
    
    def test_optimize_route_authorized(self):
        url_token = reverse('token_obtain_pair')
        response_token = self.client.post(url_token, {
            'username': 'testuser',
            'password': 'testpass123'
        })
        access_token = response_token.data['access']
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        url = reverse('api_optimize')
        response = self.client.post(url, {
            'order_id': self.order.id,
            'pickup_address': 'Москва, ул. Тверская, 1',
            'delivery_address': 'Санкт-Петербург, Невский пр., 50'
        })
        assert response.status_code == 201
        assert 'route_id' in response.data
        assert response.data['total_distance'] > 0