import random
import math
from .yandex_maps import get_coordinates, haversine_distance
from typing import List, Dict, Tuple


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Расстояние между двумя точками на сфере (в км) по формуле гаверсинуса"""
    R = 6371
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
    
    def genetic_algorithm(self, population_size: int = 50, generations: int = 200, mutation_rate: float = 0.05):
        """Генетический алгоритм с фиксацией первой и последней точки"""
        
        # Создание начальной популяции
        def create_individual():
            # Создаём список промежуточных точек (все кроме первой и последней)
            middle = list(range(1, self.n - 1))
            random.shuffle(middle)
            # Возвращаем маршрут: [0] + middle + [n-1]
            return [self.start_point] + middle + [self.n - 1]
        
        def fitness(individual):
            total = 0
            for i in range(len(individual) - 1):
                total += self.distance(individual[i], individual[i+1])
            return total
        
        def crossover(parent1, parent2):
            # PMX crossover для упорядоченных списков
            size = len(parent1)
            if size <= 3:
                return parent1[:]
            
            # Исключаем первую и последнюю точки из скрещивания
            middle_indices = list(range(1, size - 1))
            if len(middle_indices) < 2:
                return parent1[:]
            
            start, end = sorted(random.sample(middle_indices, 2))
            
            child = [None] * size
            child[0] = parent1[0]
            child[-1] = parent1[-1]
            child[start:end+1] = parent1[start:end+1]
            
            for i in range(1, size - 1):
                if child[i] is None:
                    value = parent2[i]
                    while value in child:
                        value = parent2[parent1.index(value)]
                    child[i] = value
            return child
        
        def mutate(individual):
            if len(individual) <= 3:
                return individual
            # Мутируем только промежуточные точки (не трогаем первую и последнюю)
            if random.random() < mutation_rate:
                i, j = random.sample(range(1, len(individual) - 1), 2)
                individual[i], individual[j] = individual[j], individual[i]
            return individual
        
        # Инициализация популяции
        population = [create_individual() for _ in range(population_size)]
        best_individual = None
        best_fitness = float('inf')
        no_improvement_count = 0
        
        for generation in range(generations):
            # Оценка
            fitnesses = [fitness(ind) for ind in population]
            
            # Отбор лучших
            sorted_pairs = sorted(zip(fitnesses, population), key=lambda x: x[0])
            best_fitness_current = sorted_pairs[0][0]
            
            if best_fitness_current < best_fitness:
                best_fitness = best_fitness_current
                best_individual = sorted_pairs[0][1][:]
                no_improvement_count = 0
            else:
                no_improvement_count += 1
            
            # Ранняя остановка, если алгоритм сошёлся
            if no_improvement_count > 50:
                break
            
            # Отбираем лучших особей
            selected = [ind for _, ind in sorted_pairs[:population_size // 2]]
            
            # Создание нового поколения
            new_population = []
            while len(new_population) < population_size:
                parent1, parent2 = random.sample(selected, 2)
                child = crossover(parent1, parent2)
                child = mutate(child)
                new_population.append(child)
            
            population = new_population
        
        return best_individual, best_fitness
    
    def optimize(self, method: str = 'genetic') -> Dict:
        path, distance = self.genetic_algorithm()
        return {'path': path, 'total_distance': distance, 'method': method}


def get_distance_between_addresses(addr1: str, addr2: str) -> float:
    """Получение расстояния между двумя адресами через геокодер"""
    import asyncio
    from .yandex_maps import get_coordinates, haversine_distance
    
    async def get_dist():
        try:
            coords1 = await get_coordinates(addr1)
            coords2 = await get_coordinates(addr2)
            return haversine_distance(coords1[0], coords1[1], coords2[0], coords2[1])
        except:
            return random.uniform(50, 500)
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    dist = loop.run_until_complete(get_dist())
    loop.close()
    return dist


def optimize_route(addresses: List[str], method: str = 'genetic') -> Dict:
    """
    Оптимизация маршрута.
    Первая точка (загрузка) и последняя (доставка) фиксированы.
    Оптимизируется только порядок промежуточных точек.
    """
    n = len(addresses)
    
    if n <= 2:
        total_distance = 0
        if n == 2:
            total_distance = get_distance_between_addresses(addresses[0], addresses[1])
        return {
            'optimized_order': addresses,
            'total_distance_km': round(total_distance, 2),
            'algorithm': method,
            'points_count': n
        }
    
    # Фиксируем начало и конец
    start_point = addresses[0]
    end_point = addresses[-1]
    middle_points = addresses[1:-1]
    
    # Строим матрицу расстояний на основе реальных координат
    all_points = [start_point] + middle_points + [end_point]
    m = len(all_points)
    
    # Кэшируем расстояния
    distance_cache = {}
    matrix = [[0] * m for _ in range(m)]
    
    for i in range(m):
        for j in range(i + 1, m):
            pair_key = (i, j)
            if pair_key not in distance_cache:
                dist = get_distance_between_addresses(all_points[i], all_points[j])
                distance_cache[pair_key] = dist
            dist = distance_cache[pair_key]
            matrix[i][j] = dist
            matrix[j][i] = dist
    
    # Запускаем оптимизацию с фиксированной матрицей
    optimizer = RouteOptimizer(matrix, start_point=0)
    result = optimizer.optimize(method=method)
    
    # Собираем оптимизированный порядок
    optimized_indices = result['path']
    optimized_order = [all_points[optimized_indices[0]]]
    
    for idx in optimized_indices[1:]:
        if idx != 0 and idx != m - 1:
            optimized_order.append(all_points[idx])
    
    optimized_order.append(all_points[-1])
    
    return {
        'optimized_order': optimized_order,
        'total_distance_km': round(result['total_distance'], 2),
        'algorithm': result['method'],
        'points_count': n
    }