
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
from datetime import datetime
import os
from django.conf import settings


def generate_waybill(order, route):
    """
    Генерация путевого листа в PDF с поддержкой кириллицы
    """
    
    # Регистрируем шрифт с поддержкой кириллицы
    # Используем стандартный шрифт Windows Arial или Times New Roman
    try:
        # Для Windows
        font_path = "C:/Windows/Fonts/arial.ttf"
        if not os.path.exists(font_path):
            # Альтернативный путь
            font_path = "C:/Windows/Fonts/times.ttf"
        pdfmetrics.registerFont(TTFont('Arial', font_path))
        font_name = 'Arial'
    except:
        # Если шрифт не найден, используем стандартный (латинница)
        font_name = 'Helvetica'
    
    # Создаём папку media если её нет
    media_dir = settings.MEDIA_ROOT
    if not os.path.exists(media_dir):
        os.makedirs(media_dir)
    
    filename = f"waybill_{order.order_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join(media_dir, filename)
    
    c = canvas.Canvas(filepath, pagesize=A4)
    width, height = A4
    
    # Используем зарегистрированный шрифт
    c.setFont(font_name, 18)
    c.drawString(50, height - 50, "ПУТЕВОЙ ЛИСТ")
    
    c.setFont(font_name, 10)
    c.drawString(50, height - 70, f"Дата формирования: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    c.drawString(450, height - 70, f"Номер: {route.id}")
    
    c.line(50, height - 80, width - 50, height - 80)
    
    y = height - 110
    c.setFont(font_name, 12)
    c.drawString(50, y, "1. ИНФОРМАЦИЯ О ЗАКАЗЕ")
    y -= 25
    
    c.setFont(font_name, 10)
    
    # Получаем статус на русском
    status_rus = {
        'pending': 'Ожидает',
        'loading': 'Загружается',
        'in_transit': 'В пути',
        'delivered': 'Доставлен',
        'delayed': 'Задержан',
        'damaged': 'Поврежден'
    }.get(order.status, order.status)
    
    lines = [
        f"Номер заказа: {order.order_number}",
        f"Клиент: {order.client.username}",
        f"Статус: {status_rus}",
        "",
        "2. ИНФОРМАЦИЯ О ГРУЗЕ",
        f"Наименование: {order.cargo.name}",
        f"Вес: {order.cargo.weight_kg} кг",
        f"Объем: {order.cargo.volume_m3} м3",
        f"Опасный груз: {'Да' if order.cargo.is_hazardous else 'Нет'}",
        "",
        "3. ИНФОРМАЦИЯ О ТРАНСПОРТЕ",
    ]
    
    if order.vehicle:
        type_rus = {
            'truck': 'Грузовик',
            'van': 'Фургон',
            'refrigerator': 'Рефрижератор'
        }.get(order.vehicle.type, order.vehicle.type)
        
        lines.extend([
            f"Госномер: {order.vehicle.license_plate}",
            f"Тип: {type_rus}",
            f"Грузоподъемность: {order.vehicle.capacity_kg} кг",
            f"Расход топлива: {order.vehicle.fuel_consumption} л/100км",
        ])
    else:
        lines.append("Транспорт не назначен")
    
    lines.extend([
        "",
        "4. МАРШРУТ ДВИЖЕНИЯ",
    ])
    
    for line in lines:
        c.drawString(50, y, line)
        y -= 18
        if y < 100:
            c.showPage()
            y = height - 50
            c.setFont(font_name, 10)
    
    # Точки маршрута
    c.setFont(font_name, 10)
    c.drawString(50, y, "Порядок следования:")
    y -= 18
    
    for i, addr in enumerate(route.waypoints, 1):
        if y < 80:
            c.showPage()
            y = height - 50
            c.setFont(font_name, 10)
        
        # Обрезаем слишком длинные адреса
        if len(addr) > 80:
            addr = addr[:77] + "..."
        
        icon = "1" if i == 1 else ("X" if i == len(route.waypoints) else str(i))
        c.drawString(50, y, f"{i}. {addr}")
        y -= 15
    
    y -= 10
    
    # Итоговые показатели
    c.setFont(font_name, 10)
    c.drawString(50, y, "5. ИТОГОВЫЕ ПОКАЗАТЕЛИ")
    y -= 18
    
    c.drawString(50, y, f"Общее расстояние: {route.total_distance_km} км")
    y -= 15
    c.drawString(50, y, f"Расчетное время: {route.estimated_time_min} мин")
    y -= 15
    c.drawString(50, y, f"Затраты на топливо: {route.fuel_cost} руб")
    y -= 15
    
    algo_rus = "Генетический алгоритм" if route.algorithm_used == "genetic" else "Метод ветвей и границ"
    c.drawString(50, y, f"Алгоритм оптимизации: {algo_rus}")
    y -= 15
    c.drawString(50, y, f"Эффективность: {route.optimization_score}%")
    
    # Подписи
    y -= 40
    c.line(50, y, 150, y)
    c.drawString(50, y - 10, "Диспетчер")
    
    c.line(width - 150, y, width - 50, y)
    c.drawString(width - 150, y - 10, "Водитель")
    
    c.save()
    return filepath