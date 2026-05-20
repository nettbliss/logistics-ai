import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from accounts.models import User
from core.models import Order, Cargo, Vehicle, RouteHistory
from routes.models import Route


@pytest.mark.django_db
class TestVehiclesAPI:
    """Тесты для API транспорта"""
    
    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            role='dispatcher'
        )
        
        url_token = reverse('token_obtain_pair')
        response = self.client.post(url_token, {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        
        self.vehicle = Vehicle.objects.create(
            license_plate='TEST002',
            type='truck',
            capacity_kg=8000,
            fuel_consumption=30,
            is_active=True
        )
    
    def test_get_vehicles_list(self):
        url = reverse('vehicle-list')
        response = self.client.get(url)
        assert response.status_code == 200
        assert response.data['count'] >= 1
    
    def test_create_vehicle(self):
        url = reverse('vehicle-list')
        data = {
            'license_plate': 'NEW123',
            'type': 'van',
            'capacity_kg': 1500,
            'fuel_consumption': 12.5,
            'is_active': True
        }
        response = self.client.post(url, data)
        assert response.status_code == 201
        assert response.data['license_plate'] == 'NEW123'
    
    def test_get_vehicle_detail(self):
        url = reverse('vehicle-detail', args=[self.vehicle.id])
        response = self.client.get(url)
        assert response.status_code == 200
        assert response.data['license_plate'] == 'TEST002'
    
    def test_update_vehicle(self):
        url = reverse('vehicle-detail', args=[self.vehicle.id])
        data = {'is_active': False}
        response = self.client.patch(url, data)
        assert response.status_code == 200
        assert response.data['is_active'] == False


@pytest.mark.django_db
class TestCargoAPI:
    """Тесты для API грузов"""
    
    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            role='dispatcher'
        )
        
        url_token = reverse('token_obtain_pair')
        response = self.client.post(url_token, {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        
        self.cargo = Cargo.objects.create(
            name='Test Cargo Extended',
            weight_kg=200,
            volume_m3=2.5,
            is_hazardous=True
        )
    
    def test_get_cargo_list(self):
        url = reverse('cargo-list')
        response = self.client.get(url)
        assert response.status_code == 200
    
    def test_create_cargo(self):
        url = reverse('cargo-list')
        data = {
            'name': 'New Cargo',
            'weight_kg': 500,
            'volume_m3': 3.0,
            'is_hazardous': False
        }
        response = self.client.post(url, data)
        assert response.status_code == 201
        assert response.data['name'] == 'New Cargo'
    
    def test_create_hazardous_cargo(self):
        url = reverse('cargo-list')
        data = {
            'name': 'Chemicals',
            'weight_kg': 100,
            'volume_m3': 0.5,
            'is_hazardous': True
        }
        response = self.client.post(url, data)
        assert response.status_code == 201
        assert response.data['is_hazardous'] == True


@pytest.mark.django_db
class TestRoutesAPI:
    """Тесты для API маршрутов"""
    
    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            role='client'
        )
        
        self.cargo = Cargo.objects.create(name='Cargo', weight_kg=100, volume_m3=1)
        self.vehicle = Vehicle.objects.create(
            license_plate='RT001',
            type='truck',
            capacity_kg=5000,
            fuel_consumption=25
        )
        
        self.order = Order.objects.create(
            order_number='RT-001',
            client=self.user,
            cargo=self.cargo,
            vehicle=self.vehicle,
            pickup_address='Moscow, Start',
            delivery_address='Moscow, End'
        )
        
        self.route = Route.objects.create(
            order=self.order,
            vehicle=self.vehicle,
            total_distance_km=100.5,
            estimated_time_min=90,
            fuel_cost=5000,
            waypoints=['Moscow, Start', 'Moscow, Middle', 'Moscow, End'],
            algorithm_used='genetic',
            optimization_score=15.5
        )
        
        url_token = reverse('token_obtain_pair')
        response = self.client.post(url_token, {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
    
    def test_get_routes_list(self):
        url = reverse('route-list')
        response = self.client.get(url)
        assert response.status_code == 200
        assert response.data['count'] >= 1
    
    def test_get_route_detail(self):
        url = reverse('route-detail', args=[self.route.id])
        response = self.client.get(url)
        assert response.status_code == 200
        assert response.data['total_distance_km'] == 100.5
    
    def test_route_has_order_info(self):
        url = reverse('route-detail', args=[self.route.id])
        response = self.client.get(url)
        assert 'order' in response.data
        assert response.data['order_number'] is not None


@pytest.mark.django_db
class TestOrderWorkflow:
    """Полный цикл работы с заказом"""
    
    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            role='client'
        )
        
        self.cargo = Cargo.objects.create(name='Workflow Cargo', weight_kg=300, volume_m3=2)
        self.vehicle = Vehicle.objects.create(
            license_plate='WF001',
            type='refrigerator',
            capacity_kg=3000,
            fuel_consumption=28
        )
        
        url_token = reverse('token_obtain_pair')
        response = self.client.post(url_token, {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
    
    def test_full_order_lifecycle(self):
        # 1. Создание заказа
        create_url = reverse('order-list')
        order_data = {
            'order_number': 'WF-001',
            'client': self.user.id,
            'cargo': self.cargo.id,
            'vehicle': self.vehicle.id,
            'pickup_address': 'Moscow, Pickup',
            'delivery_address': 'Moscow, Delivery',
            'status': 'pending'
        }
        create_response = self.client.post(create_url, order_data)
        assert create_response.status_code == 201
        order_id = create_response.data['id']
        
        # 2. Оптимизация маршрута
        opt_url = reverse('api_optimize')
        opt_data = {
            'order_id': order_id,
            'pickup_address': 'Moscow, Pickup',
            'delivery_address': 'Moscow, Delivery'
        }
        opt_response = self.client.post(opt_url, opt_data, format='json')
        assert opt_response.status_code == 201
        assert 'route_id' in opt_response.data
        
        # 3. Проверка что маршрут создан
        route_id = opt_response.data['route_id']
        route_url = reverse('route-detail', args=[route_id])
        route_response = self.client.get(route_url)
        assert route_response.status_code == 200
        
        # 4. Проверка истории
        history_url = reverse('routehistory-list')
        history_response = self.client.get(history_url)
        assert history_response.status_code == 200
    
    def test_optimize_without_addresses(self):
        order = Order.objects.create(
            order_number='WF-002',
            client=self.user,
            cargo=self.cargo,
            vehicle=self.vehicle,
            pickup_address='Moscow, Pickup 2',
            delivery_address='Moscow, Delivery 2'
        )
        
        url = reverse('api_optimize')
        data = {'order_id': order.id}
        response = self.client.post(url, data, format='json')
        assert response.status_code == 201
        assert 'route_id' in response.data
    
    def test_optimize_updates_order_addresses(self):
        order = Order.objects.create(
            order_number='WF-003',
            client=self.user,
            cargo=self.cargo,
            vehicle=self.vehicle,
            pickup_address='Old Pickup',
            delivery_address='Old Delivery'
        )
        
        url = reverse('api_optimize')
        data = {
            'order_id': order.id,
            'pickup_address': 'New Pickup',
            'delivery_address': 'New Delivery'
        }
        response = self.client.post(url, data, format='json')
        assert response.status_code == 201
        
        order.refresh_from_db()
        assert order.pickup_address == 'New Pickup'
        assert order.delivery_address == 'New Delivery'


@pytest.mark.django_db
class TestEdgeCases:
    """Граничные случаи и ошибки"""
    
    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            role='client'
        )
        
        self.cargo = Cargo.objects.create(name='Edge Cargo', weight_kg=100, volume_m3=1)
        self.vehicle = Vehicle.objects.create(
            license_plate='ED001',
            type='truck',
            capacity_kg=1000,
            fuel_consumption=20
        )
        
        url_token = reverse('token_obtain_pair')
        response = self.client.post(url_token, {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
    
    def test_optimize_missing_order_id(self):
        url = reverse('api_optimize')
        data = {}
        response = self.client.post(url, data, format='json')
        assert response.status_code == 400
        assert 'error' in response.data
    
    def test_optimize_invalid_order_id(self):
        url = reverse('api_optimize')
        data = {'order_id': 99999}
        response = self.client.post(url, data, format='json')
        assert response.status_code == 404
    
    def test_create_order_duplicate_number(self):
        order1 = Order.objects.create(
            order_number='DUPLICATE',
            client=self.user,
            cargo=self.cargo,
            vehicle=self.vehicle,
            pickup_address='Addr1',
            delivery_address='Addr2'
        )
        
        url = reverse('order-list')
        data = {
            'order_number': 'DUPLICATE',
            'client': self.user.id,
            'cargo': self.cargo.id,
            'vehicle': self.vehicle.id,
            'pickup_address': 'Addr3',
            'delivery_address': 'Addr4'
        }
        response = self.client.post(url, data)
        assert response.status_code == 400
    
    def test_get_nonexistent_route(self):
        url = reverse('route-detail', args=[99999])
        response = self.client.get(url)
        assert response.status_code == 404
    
    def test_optimize_with_waypoints_only(self):
        order = Order.objects.create(
            order_number='ED-001',
            client=self.user,
            cargo=self.cargo,
            vehicle=self.vehicle,
            pickup_address='Start',
            delivery_address='End'
        )
        
        url = reverse('api_optimize')
        data = {
            'order_id': order.id,
            'waypoints': ['Point 1', 'Point 2', 'Point 3']
        }
        response = self.client.post(url, data, format='json')
        assert response.status_code == 201
        assert len(response.data['optimized_order']) >= 5