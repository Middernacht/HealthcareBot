import requests
import logging
from config import WEATHER_API_KEY


def get_weather(city):
    """Получение текущей погоды в городе."""
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
        response = requests.get(url)
        data = response.json()
        if response.status_code == 200:
            return data["main"]["temp"]
        else:
            return None
    except Exception as e:
        logging.error(f"Ошибка при получении погоды: {e}")
        return None


def calculate_norms(user_info):
    """Расчёт дневных норм воды и калорий."""
    weight = user_info.get("weight", 0)
    height = user_info.get("height", 0)
    age = user_info.get("age", 0)
    city = user_info.get("city", "")

    # Примерные формулы для расчёта
    water_norm = weight * 30  # 30 мл воды на кг массы тела
    calories_norm = 10 * weight + 6.25 * height - 5 * age + 5  # Формула Миффлина-Сан Жеора для мужчин

    # Учет температуры
    temperature = get_weather(city)
    print(temperature)
    if temperature and temperature > 25:
        water_norm += 750  # Добавляем 750 мл при температуре выше 25°C

    return {
        "water": round(water_norm, 2),
        "calories": round(calories_norm, 2),
        "temperature": temperature
    }


def get_food_calories(product_name):
    url = f"https://world.openfoodfacts.org/cgi/search.pl?action=process&search_terms={product_name}&json=true"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        products = data.get('products', [])
        if products:  # Проверяем, есть ли найденные продукты
            first_product = products[0]
            return {
                'name': first_product.get('product_name', 'Неизвестно'),
                'calories': first_product.get('nutriments', {}).get('energy-kcal_100g', 0)
            }
        return None
    print(f"Ошибка: {response.status_code}")
    return None


def calculate_workout_calories(workout, duration, weight):
    """Примерный расчёт калорий, сожжённых за тренировку."""
    workout_met = {
        "бег": 9.8,
        "ходьба": 3.8,
        "велосипед": 7.5,
        "плавание": 8.0
    }
    met = workout_met.get(workout.lower(), 5)  # Среднее значение MET, если тренировка не найдена
    calories_burned = (met * 3.5 * weight / 200) * duration
    return round(calories_burned, 2)
