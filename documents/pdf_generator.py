from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import os
from django.conf import settings


def generate_waybill(order, route):
    """
    Генерация путевого листа в PDF с поддержкой кириллицы
    """
    # Создаём папку media если её нет
    media_dir = settings.MEDIA_ROOT
    if not os.path.exists(media_dir):
        os.makedirs(media_dir)
    
    filename = f"waybill_{order.order_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join(media_dir, filename)
    
    # Регистрируем шрифт с поддержкой кириллицы
    try:
        # Для Windows
        font_path = "C:/Windows/Fonts/arial.ttf"
        if not os.path.exists(font_path):
            font_path = "C:/Windows/Fonts/times.ttf"
        pdfmetrics.registerFont(TTFont('Arial', font_path))
        font_name = 'Arial'
    except:
        font_name = 'Helvetica'
    
    c = canvas.Canvas(filepath, pagesize=A4)
    width, height = A4
    
    # Шапка
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
    
    # Статус на русском
    status_names = {
        'pending': 'Ожидает',
        'loading': 'Загружается',
        'in_transit': 'В пути',
        'delivered': 'Доставлен',
        'delayed': 'Задержан',
        'damaged': 'Повреждён',
    }
    status_rus = status_names.get(order.status, order.status)
    
    lines = [
        f"Номер заказа: {order.order_number}",
        f"Клиент: {order.client.username}",
        f"Статус: {status_rus}",
        "",
        "2. ИНФОРМАЦИЯ О ГРУЗЕ",
        f"Наименование: {order.cargo.name}",
        f"Вес: {order.cargo.weight_kg} кг",
        f"Объём: {order.cargo.volume_m3} м3",
        f"Опасный груз: {'Да' if order.cargo.is_hazardous else 'Нет'}",
        "",
        "3. ИНФОРМАЦИЯ О ТРАНСПОРТЕ",
    ]
    
    if order.vehicle:
        type_names = {'truck': 'Грузовик', 'van': 'Фургон', 'refrigerator': 'Рефрижератор'}
        type_rus = type_names.get(order.vehicle.type, order.vehicle.type)
        lines.extend([
            f"Госномер: {order.vehicle.license_plate}",
            f"Тип: {type_rus}",
            f"Грузоподъёмность: {order.vehicle.capacity_kg} кг",
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
        display_addr = addr[:80] + "..." if len(addr) > 80 else addr
        c.drawString(50, y, f"{i}. {display_addr}")
        y -= 15
    
    y -= 10
    
    # Итоговые показатели
    c.setFont(font_name, 10)
    c.drawString(50, y, "5. ИТОГОВЫЕ ПОКАЗАТЕЛИ")
    y -= 18
    
    c.drawString(50, y, f"Общее расстояние: {route.total_distance_km} км")
    y -= 15
    c.drawString(50, y, f"Расчётное время: {route.estimated_time_min} мин")
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