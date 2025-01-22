from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from states import Form
from utils import calculate_norms, calculate_workout_calories, get_food_calories


router = Router()

user_data = {}

# Обработчик команды /start
@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.reply("Добро пожаловать! Я ваш бот.\nВведите /help для списка команд.")

# Обработчик команды /help
@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.reply(
        "Доступные команды:\n"
        "/start - Начало работы\n"
        "/set_profile - Заполнить профиль\n"
        "/log_food - Получить расчет калорий\n"
        "/log_water - Получить расчет воды\n"
        "/log_workout - Записать активность\n"
        "/check_progress - Получить сводку прогресса"
    )

# FSM: диалог с пользователем
@router.message(Command("set_profile"))
async def set_profile(message: Message, state: FSMContext):
    await message.reply("Какой у вас вес?")
    await state.set_state(Form.weight)

@router.message(Form.weight)
async def profile_weight(message: Message, state: FSMContext):
    try:
        user_data[message.from_user.id] = {"weight": float(message.text)}
        await message.reply("Какой у вас рост?")
        await state.set_state(Form.height)
    except ValueError:
        await message.reply("Какой у вас вес? (Введите число)")
        await state.set_state(Form.weight)

@router.message(Form.height)
async def profile_height(message: Message, state: FSMContext):
    try:
        user_data[message.from_user.id]["height"] = float(message.text)
        await message.reply("Сколько вам лет?")
        await state.set_state(Form.age)
    except ValueError:
        await message.reply("Какой у вас рост? (Введите число)")
        await state.set_state(Form.height)

@router.message(Form.age)
async def profile_age(message: Message, state: FSMContext):
    try:
        user_data[message.from_user.id]["age"] = int(message.text)
        await message.reply("Сколько минут активности у вас в день?")
        await state.set_state(Form.activity)
    except ValueError:
        await message.reply("Сколько вам лет? (Введите целое число)")
        await state.set_state(Form.age)

@router.message(Form.activity)
async def profile_activity(message: Message, state: FSMContext):
    try:
        user_data[message.from_user.id]["activity"] = int(message.text)
        await message.reply("В каком городе вы находитесь?")
        await state.set_state(Form.city)
    except ValueError:
        await message.reply("Сколько минут активности у вас в день?")
        await state.set_state(Form.activity)

@router.message(Form.city)
async def profile_city(message: Message, state: FSMContext):
    try:
        user_data[message.from_user.id]["city"] = message.text
        await message.reply("Каково целевое значение калорий? Для автоматического вычисления цели напишите 'auto'")
        await state.set_state(Form.goal)
    except ValueError:
        await message.reply("В каком городе вы находитесь?")
        await state.set_state(Form.city)

@router.message(Form.goal)
async def profile_goal(message: Message, state: FSMContext):
    try:
        user_id = message.from_user.id
        norms = calculate_norms(user_data[user_id])
        if message.text != "auto":
            user_data[user_id]["calorie_goal"] = int(message.text)
        else:
            user_data[user_id]["calorie_goal"] = norms['calories']
        user_data[user_id]["water_goal"] = norms['water']
        user_data[user_id]["logged_water"] = 0
        user_data[user_id]["logged_calories"] = 0
        user_data[user_id]["burned_calories"] = 0
        await message.reply(
            f"Ваша дневная норма воды: {norms['water']} мл\nВаша дневная норма калорий: {norms['calories']} ккал")
        if norms.get('temperature'):
            await message.reply(f"Текущая температура в вашем городе: {norms['temperature']}°C")
        await state.clear()
    except ValueError:
        await message.reply("Какова ваша цель?")
        await state.set_state(Form.goal)


@router.message(Command("log_water"))
async def log_water(message: Message):
    try:
        user_id = message.from_user.id
        amount = float(message.text.split()[1])
        user_data[user_id]["logged_water"] += amount
        logged = user_data[user_id]['logged_water']
        goal = user_data[user_id]['water_goal']
        await message.reply(f"- Выпито: {logged} мл из {goal} мл.\n- Осталось: {goal - logged} мл.")
    except ValueError:
        await message.reply("Неверный формат данных")


@router.message(Command("log_food"))
async def log_food(message: Message):
    try:
        user_id = message.from_user.id
        dish = ' '.join(message.text.split()[1:-1])
        weight = float(message.text.split()[-1])
        amount = get_food_calories(dish)["calories"] * weight / 100
        user_data[user_id]["logged_calories"] += amount
        logged = user_data[user_id]['logged_calories']
        goal = user_data[user_id]['calorie_goal']
        burned = user_data[user_id]['burned_calories']
        await message.reply(f"- Записано: {amount} ккал.\n- Потреблено: {logged} ккал из {goal} ккал.\n- Сожжено: {burned} ккал.\n- Осталось: {goal - logged + burned} ккал.")
    except ValueError:
        await message.reply("Неверный формат данных")


@router.message(Command("log_workout"))
async def log_workout(message: Message):
    try:
        user_id = message.from_user.id
        sport = ' '.join(message.text.split()[1:-1])
        duration = float(message.text.split()[-1])
        weight = user_data[user_id]['weight']
        amount = calculate_workout_calories(sport, duration, weight)
        user_data[user_id]["burned_calories"] += amount
        user_data[user_id]["water_goal"] += 200 * (duration // 30)
        logged = user_data[user_id]['logged_calories']
        goal = user_data[user_id]['calorie_goal']
        burned = user_data[user_id]['burned_calories']
        await message.reply(f"- Записано: {amount} ккал.\n- Потреблено: {logged} ккал из {goal} ккал.\n- Сожжено: {burned} ккал.\n- Осталось: {goal - logged + burned} ккал.")
    except ValueError:
        await message.reply("Неверный формат данных")


@router.message(Command("check_progress"))
async def check_progress(message: Message):
    try:
        user_id = message.from_user.id
        logged = user_data[user_id]['logged_calories']
        goal = user_data[user_id]['calorie_goal']
        burned = user_data[user_id]['burned_calories']
        logged_water = user_data[user_id]['logged_water']
        goal_water = user_data[user_id]['water_goal']
        await message.reply(
            f"📊 Прогресс:\n"
            "Вода:\n"
            f"- Выпито: {logged_water} мл из {goal_water} мл.\n"
            f"- Осталось: {goal_water - logged_water} мл."
            "Калории:\n"
            f"- Потреблено: {logged} ккал из {goal} ккал.\n"
            f"- Сожжено: {burned} ккал.\n"
            f"- Осталось: {goal - logged + burned} ккал."
        )
    except ValueError:
        await message.reply("Неверный формат данных")

# Функция для подключения обработчиков
def setup_handlers(dp):
    dp.include_router(router)