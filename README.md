# OptiRoute — интеллектуальная логистическая платформа

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.2-green.svg)](https://www.djangoproject.com/)

## О проекте

OptiRoute — это веб-приложение для оптимизации маршрутов доставки с использованием генетического алгоритма. Система позволяет автоматически строить оптимальные маршруты для мультиточечных перевозок, визуализировать их на карте и оценивать экономическую эффективность.

### Основные возможности

- Генетический алгоритм для оптимизации маршрутов
- Визуализация на Яндекс.Картах
- Сравнение обычного и оптимизированного маршрута
- Генерация путевых листов в PDF
- REST API с JWT-авторизацией
- История всех рассчитанных маршрутов

## Технологии

- **Backend**: Django 5.2, Django REST Framework, JWT
- **Frontend**: HTML5, CSS3, JavaScript, Яндекс.Карты API
- **Database**: SQLite / PostgreSQL
- **Deployment**: Docker, Gunicorn

## Установка и запуск

# Клонирование

git clone https://github.com/nettbliss/logistics-ai.git
cd logistics-ai

# Создание виртуального окружения

python -m venv venv
venv\Scripts\activate # Windows
source venv/bin/activate # Linux/Mac

# Установка зависимостей

pip install -r requirements.txt

# Миграции

python manage.py migrate

# Создание суперпользователя

python manage.py createsuperuser

# Запуск

python manage.py runserver

## Запуск через Docker

# Клонирование

git clone https://github.com/nettbliss/logistics-ai.git
cd logistics-ai

# Сборка и запуск

docker-compose up --build

# Или только сборка образа

docker build -t optiroute .

# Запуск контейнера

docker run -p 8000:8000 optiroute
После запуска открой в браузере: http://127.0.0.1:8000/multi/

# API Примеры

Получение токена
curl -X POST http://127.0.0.1:8000/api/token/ \
 -H "Content-Type: application/json" \
 -d '{"username":"admin","password":"admin123"}'

Оптимизация маршрута
curl -X POST http://127.0.0.1:8000/api/optimize/ \
 -H "Authorization: Bearer your_access_token" \
 -H "Content-Type: application/json" \
 -d '{
"order_id": 1,
"pickup_address": "Москва, ул. Тверская, 1",
"delivery_address": "Санкт-Петербург, Невский пр., 50",
"waypoints": ["Тверь, ул. Революции, 12"]
}'
Список заказов
curl -X GET http://127.0.0.1:8000/api/orders/ \
 -H "Authorization: Bearer your_access_token"
