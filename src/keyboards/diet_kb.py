from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def start_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Начать", callback_data="start_profile")]
    ])


def gender_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Мужской", callback_data="gender:male"),
            InlineKeyboardButton(text="Женский", callback_data="gender:female"),
        ]
    ])


def goal_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="−2 кг", callback_data="goal:-2")],
        [InlineKeyboardButton(text="−5 кг", callback_data="goal:-5")],
        [InlineKeyboardButton(text="−10 кг", callback_data="goal:-10")],
        [InlineKeyboardButton(text="−15 кг и более", callback_data="goal:-15")],
    ])


def activity_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Малоподвижный (офис, редко хожу)", callback_data="activity:low")],
        [InlineKeyboardButton(text="Умеренно активный (1-3 тренировки/нед.)", callback_data="activity:medium")],
        [InlineKeyboardButton(text="Активный (4+ тренировок/нед.)", callback_data="activity:high")],
    ])


def skip_kb(callback: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Нет / Пропустить", callback_data=callback)]
    ])


def returning_user_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🥗 Получить рацион на сегодня", callback_data="diet:generate_existing")],
        [InlineKeyboardButton(text="🧊 Что приготовить из холодильника?", callback_data="fridge:open")],
        [InlineKeyboardButton(text="✏️ Обновить мои данные", callback_data="diet:restart")],
    ])


def diet_actions_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Другой вариант", callback_data="diet:alternative")],
        [InlineKeyboardButton(text="Изменить данные", callback_data="diet:restart")],
    ])
