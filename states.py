from aiogram.fsm.state import State, StatesGroup

class Form(StatesGroup):
    name = State()
    age = State()
    weight = State()
    height = State()
    city = State()
    activity = State()
    goal = State()
