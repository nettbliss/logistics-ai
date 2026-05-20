import aiohttp

async def get_coordinates(address: str) -> tuple:
    """Получение координат адреса через Яндекс.Геокодер"""
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


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Расстояние между двумя точками на сфере (в км)"""
    import math
    R = 6371
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c