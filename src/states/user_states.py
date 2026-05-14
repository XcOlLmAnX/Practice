from aiogram.fsm.state import State, StatesGroup


class ProfileStates(StatesGroup):
    name = State()
    gender = State()
    age = State()
    height = State()
    weight = State()
    goal = State()
    activity = State()
    restrictions = State()
    preferences = State()


class FridgeStates(StatesGroup):
    waiting_products = State()
