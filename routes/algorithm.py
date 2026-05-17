import random
import math
from typing import List, Dict, Tuple


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Расстояние между двумя точками на сфере (в км) по формуле гаверсинуса
    """
    R = 6371  # Радиус Земли в км
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c


class RouteOptimizer:
    def __init__(self, matrix: List[List[float]], start_point: int = 0):
        self.matrix = matrix
        self.start_point = start_point
        self.n = len(matrix)
    
    def distance(self, a: int, b: int) -> float:
        return self.matrix[a][b]
    
    def genetic_algorithm(self, population_size: int = 30, generations: int = 100, mutation_rate: float = 0.1):
        if population_size > self.n * 10:
            population_size = max(10, self.n * 2)
        
        def create_individual():
            # Создаём маршрут, где start_point всегда первый
            individual = list(range(self.n))
            random.shuffle(individual)
            if self.start_point in individual:
                individual.remove(self.start_point)
                individual.insert(0, self.start_point)
            return individual
        
        def fitness(individual):
            total = 0
            for i in range(len(individual) - 1):
                total += self.distance(individual[i], individual[i+1])
            return max(total, 0.01)
        
        def crossover(parent1, parent2):
            size = len(parent1)
            if size <= 2:
                return parent1[:]
            try:
                start, end = sorted(random.sample(range(1, size), 2))
            except ValueError:
                return parent1[:]
            
            child = [None] * size
            child[0] = self.start_point  # Первая точка фиксирована
            child[start:end+1] = parent1[start:end+1]
            
            for i in range(size):
                if child[i] is None and i != 0:
                    value = parent2[i]
                    while value in child and value is not None:
                        try:
                            value = parent2[parent1.index(value)]
                        except ValueError:
                            break
                    child[i] = value
            return child
        
        def mutate(individual):
            if len(individual) <= 2:
                return individual
            if random.random() < mutation_rate:
                # Мутируем только промежуточные точки (не трогаем первую)
                i, j = random.sample(range(1, len(individual)), 2)
                individual[i], individual[j] = individual[j], individual[i]
            return individual
        
        # Инициализация
        try:
            population = [create_individual() for _ in range(population_size)]
        except Exception:
            population = [list(range(self.n)) for _ in range(population_size)]
        
        for _ in range(generations):
            fitnesses = [fitness(ind) for ind in population]
            sorted_indices = sorted(range(len(population)), key=lambda i: fitnesses[i])
            population = [population[i] for i in sorted_indices[:max(2, population_size//2)]]
            
            new_population = []
            while len(new_population) < population_size:
                if len(population) >= 2:
                    p1, p2 = random.sample(population, 2)
                    child = crossover(p1, p2)
                    child = mutate(child)
                    new_population.append(child)
                else:
                    new_population.append(create_individual())
            population = new_population
        
        best_individual = min(population, key=fitness)
        return best_individual, fitness(best_individual)
    
    def optimize(self, method: str = 'genetic') -> Dict:
        path, distance = self.genetic_algorithm()
        return {'path': path, 'total_distance': distance, 'method': method}


async def get_coordinates(address: str) -> tuple:
    """
    Получение координат адреса через Яндекс.Геокодер (асинхронно)
    Используется в views.py
    """
    from django.conf import settings
    import aiohttp
    
    # Базовый URL геокодера
    url = "https://geocode-maps.yandex.ru/1.x/"
    params = {
        "apikey": "8c37cabe-5660-4967-9266-0b2af004ea7d",
        "geocode": address,
        "format": "json",
        "results": 1
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            data = await response.json()
            try:
                point = data["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]["Point"]["pos"]
                lon, lat = map(float, point.split())
                return (lat, lon)
            except (KeyError, IndexError):
                raise ValueError(f"Адрес не найден: {address}")


def calculate_real_distance_matrix(coordinates: List[tuple]) -> List[List[float]]:
    """
    Рассчитывает матрицу расстояний на основе реальных координат
    coordinates: список кортежей (широта, долгота)
    """
    n = len(coordinates)
    matrix = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            lat1, lon1 = coordinates[i]
            lat2, lon2 = coordinates[j]
            dist = haversine_distance(lat1, lon1, lat2, lon2)
            matrix[i][j] = dist
            matrix[j][i] = dist
    return matrix


def optimize_route_with_real_distances(addresses: List[str], coordinates: List[tuple], method: str = 'genetic') -> Dict:
    """
    Оптимизация маршрута с реальными расстояниями
    addresses: список адресов
    coordinates: список координат (широта, долгота) для каждого адреса
    """
    n = len(addresses)
    
    if n <= 2:
        return {
            'optimized_order': addresses,
            'total_distance_km': 0 if n <= 1 else round(haversine_distance(
                coordinates[0][0], coordinates[0][1],
                coordinates[1][0], coordinates[1][1]
            ), 2),
            'algorithm': method,
            'points_count': n
        }
    
    # Фиксируем начало и конец
    start_point = addresses[0]
    end_point = addresses[-1]
    middle_addresses = addresses[1:-1]
    middle_coords = coordinates[1:-1]
    
    if len(middle_addresses) <= 1:
        total_dist = 0
        for i in range(len(coordinates) - 1):
            total_dist += haversine_distance(
                coordinates[i][0], coordinates[i][1],
                coordinates[i+1][0], coordinates[i+1][1]
            )
        return {
            'optimized_order': addresses,
            'total_distance_km': round(total_dist, 2),
            'algorithm': method,
            'points_count': n
        }
    
    # Строим матрицу расстояний для всех точек
    all_coords = coordinates
    m = len(all_coords)
    matrix = [[0] * m for _ in range(m)]
    for i in range(m):
        for j in range(i + 1, m):
            dist = haversine_distance(
                all_coords[i][0], all_coords[i][1],
                all_coords[j][0], all_coords[j][1]
            )
            matrix[i][j] = dist
            matrix[j][i] = dist
    
    # Запускаем оптимизацию
    optimizer = RouteOptimizer(matrix, start_point=0)
    result = optimizer.optimize(method=method)
    
    # Собираем оптимизированный порядок
    optimized_path = result['path']
    optimized_order = [addresses[optimized_path[0]]]  # первая точка
    
    for idx in optimized_path[1:]:
        if idx != 0 and idx != m - 1:
            optimized_order.append(addresses[idx])
    
    optimized_order.append(addresses[-1])  # последняя точка фиксирована
    
    return {
        'optimized_order': optimized_order,
        'total_distance_km': round(result['total_distance'], 2),
        'algorithm': result['method'],
        'points_count': n
    }


# Функция для обратной совместимости (с симуляцией)
def optimize_route(addresses: List[str], method: str = 'genetic') -> Dict:
    """
    Упрощённая версия с симуляцией расстояний (для тестов)
    """
    n = len(addresses)
    
    if n <= 1:
        return {
            'optimized_order': addresses,
            'total_distance_km': 0,
            'algorithm': method,
            'points_count': n
        }
    
    matrix = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            dist = random.uniform(10, 100)
            matrix[i][j] = dist
            matrix[j][i] = dist
    
    optimizer = RouteOptimizer(matrix, start_point=0)
    result = optimizer.optimize(method=method)
    
    optimized_addresses = [addresses[i] for i in result['path']]
    
    return {
        'optimized_order': optimized_addresses,
        'total_distance_km': round(result['total_distance'], 2),
        'algorithm': result['method'],
        'points_count': n
    }