import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from accounts.models import User
from core.models import Cargo, Vehicle, Order, RouteHistory
from routes.models import Route
from datetime import timedelta

class Command(BaseCommand):
    help = 'Generate large test data for demonstration'

    def handle(self, *args, **kwargs):
        self.stdout.write('Generating test data...')
        
        # Очищаем старые заказы и маршруты
        self.stdout.write('Cleaning old orders and routes...')
        RouteHistory.objects.all().delete()
        Route.objects.all().delete()
        Order.objects.all().delete()
        
        # Создаём пользователя client если нет
        client, created = User.objects.get_or_create(
            username='test_client',
            defaults={
                'email': 'test@example.com',
                'role': 'client',
                'is_active': True,
                'password': make_password('test123')
            }
        )
        if created:
            self.stdout.write('Created test_client user')
        
        # Создаём пользователя admin2 если нет
        admin2, created = User.objects.get_or_create(
            username='admin2',
            defaults={
                'email': 'admin2@example.com',
                'role': 'dispatcher',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
                'password': make_password('admin123')
            }
        )
        if created:
            self.stdout.write('Created admin2 user')
        
        # Создаём грузы
        cargo_items = [
            ('Строительные материалы', 1500, 4.5, False, False),
            ('Продукты питания', 800, 3.2, False, True),
            ('Химические реагенты', 500, 1.2, True, False),
            ('Мебель', 2000, 8.0, False, False),
            ('Электроника', 300, 1.5, False, False),
            ('Одежда', 400, 3.0, False, False),
            ('Книги', 600, 2.5, False, False),
            ('Запчасти', 700, 1.8, False, False),
            ('Лекарства', 200, 1.0, False, True),
            ('Нефтепродукты', 1000, 2.0, True, False),
            ('Цемент', 2500, 3.5, False, False),
            ('Песок', 3000, 4.0, False, False),
            ('Овощи', 900, 4.5, False, True),
            ('Фрукты', 700, 3.8, False, True),
            ('Молоко', 500, 2.5, False, True),
        ]
        
        for name, weight, volume, hazardous, temp in cargo_items:
            Cargo.objects.get_or_create(
                name=name,
                defaults={
                    'weight_kg': weight,
                    'volume_m3': volume,
                    'is_hazardous': hazardous,
                    'requires_temperature': temp
                }
            )
        self.stdout.write(f'Cargo count: {Cargo.objects.count()}')
        
        # Создаём транспорт
        vehicles_data = [
            ('А123ВС', 'truck', 5000, 25.5, True),
            ('В456ОЕ', 'refrigerator', 3500, 28.0, True),
            ('С789РР', 'van', 1200, 15.2, True),
            ('Е012КК', 'truck', 8000, 32.0, True),
            ('Н345ММ', 'refrigerator', 2500, 24.0, True),
            ('Р678НН', 'van', 900, 12.5, True),
            ('Т901ПП', 'truck', 6000, 27.0, True),
            ('У234РР', 'refrigerator', 4000, 30.0, True),
            ('Ф567СС', 'van', 1500, 14.0, True),
            ('Х890ТТ', 'truck', 7000, 29.0, True),
        ]
        
        for plate, vtype, capacity, fuel, active in vehicles_data:
            Vehicle.objects.get_or_create(
                license_plate=plate,
                defaults={
                    'type': vtype,
                    'capacity_kg': capacity,
                    'fuel_consumption': fuel,
                    'is_active': active
                }
            )
        self.stdout.write(f'Vehicles count: {Vehicle.objects.count()}')
        
        # Адреса
        addresses = {
            'Москва': ['ул. Тверская, 12', 'ул. Ленина, 5', 'МКАД 24-й км', 'ул. Варшавская, 45', 'пр. Мира, 10'],
            'Санкт-Петербург': ['Невский пр., 50', 'ул. Садовая, 15', 'пр. Просвещения, 30', 'ул. Ленина, 100'],
            'Казань': ['ул. Баумана, 15', 'пр. Ямашева, 20', 'ул. Кремлёвская, 5'],
            'Екатеринбург': ['ул. Ленина, 45', 'пр. Ленина, 100', 'ул. Малышева, 50'],
            'Новосибирск': ['Красный пр., 100', 'ул. Ленина, 20', 'пр. Димитрова, 15'],
            'Нижний Новгород': ['ул. Большая Покровская, 10', 'пр. Гагарина, 25'],
            'Краснодар': ['ул. Красная, 120', 'ул. Северная, 45'],
            'Воронеж': ['ул. Плехановская, 12', 'пр. Революции, 30'],
            'Тверь': ['ул. Революции, 10', 'пр. Чайковского, 5'],
            'Тула': ['пр. Ленина, 30', 'ул. Советская, 8'],
            'Ярославль': ['ул. Свободы, 8', 'пр. Ленина, 20'],
            'Пермь': ['ул. Ленина, 100', 'ул. Пушкина, 45'],
            'Ростов-на-Дону': ['ул. Большая Садовая, 65', 'пр. Ворошиловский, 20'],
            'Самара': ['ул. Ленина, 50', 'пр. Кирова, 30'],
            'Уфа': ['пр. Октября, 10', 'ул. Ленина, 60'],
        }
        
        cities = list(addresses.keys())
        all_cargos = list(Cargo.objects.all())
        all_vehicles = list(Vehicle.objects.all())
        
        if not all_cargos or not all_vehicles:
            self.stdout.write(self.style.ERROR('No cargo or vehicles found!'))
            return
        
        # Создаём заказы
        self.stdout.write('Creating orders...')
        statuses = ['pending', 'loading', 'in_transit', 'delivered', 'delayed']
        order_count = 50
        
        for i in range(order_count):
            pickup_city = random.choice(cities)
            delivery_city = random.choice([c for c in cities if c != pickup_city])
            
            pickup_address = f"{pickup_city}, {random.choice(addresses[pickup_city])}"
            delivery_address = f"{delivery_city}, {random.choice(addresses[delivery_city])}"
            
            # Промежуточные точки
            num_waypoints = random.randint(0, 3)
            waypoints = []
            available = [c for c in cities if c not in [pickup_city, delivery_city]]
            for _ in range(num_waypoints):
                if available:
                    wp_city = random.choice(available)
                    waypoints.append(f"{wp_city}, {random.choice(addresses[wp_city])}")
                    available.remove(wp_city)
            
            status = random.choice(statuses)
            days_ago = random.randint(0, 60)
            
            order = Order.objects.create(
                order_number=f"ORD-{i+1:04d}",
                client=client,
                cargo=random.choice(all_cargos),
                vehicle=random.choice(all_vehicles),
                pickup_address=pickup_address,
                delivery_address=delivery_address,
                waypoints=waypoints,
                status=status,
                created_at=timezone.now() - timedelta(days=days_ago)
            )
            
            # Для 60% заказов создаём маршруты
            if random.random() < 0.6:
                all_addresses = [pickup_address] + waypoints + [delivery_address]
                total_distance = random.uniform(100, 2000)
                optimized_distance = total_distance * random.uniform(0.7, 0.95)
                
                route = Route.objects.create(
                    order=order,
                    vehicle=order.vehicle,
                    total_distance_km=round(optimized_distance, 2),
                    estimated_time_min=int(optimized_distance * random.uniform(0.8, 1.5)),
                    fuel_cost=round(optimized_distance * 50, 2),
                    waypoints=all_addresses,
                    algorithm_used='genetic',
                    optimization_score=round((total_distance - optimized_distance) / total_distance * 100, 2)
                )
                
                RouteHistory.objects.create(
                    order=order,
                    optimized_order=all_addresses,
                    total_distance_km=round(optimized_distance, 2),
                    algorithm_used='genetic',
                    calculation_time_ms=random.uniform(50, 500),
                    economy_percent=route.optimization_score
                )
        
        self.stdout.write(self.style.SUCCESS(f'Orders created: {Order.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'Routes created: {Route.objects.count()}'))