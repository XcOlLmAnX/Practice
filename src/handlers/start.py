from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from keyboards.diet_kb import start_kb, returning_user_kb
from database.db import get_user

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    user = await get_user(message.from_user.id)

    if user:
        await message.answer(
            f"С возвращением, {user['name']}! 👋\n\n"
            f"Твои данные уже сохранены:\n"
            f"⚖️ Вес: {user['weight']} кг  📏 Рост: {user['height']} см\n"
            f"🎯 Цель: сбросить {user['goal']} кг  🔥 Калорий в день: {user['target_calories']} ккал\n\n"
            f"Что делаем?",
            reply_markup=returning_user_kb(),
        )
    else:
        await message.answer(
            "Привет! Я FitBot — твой личный помощник по питанию для похудения. 🥗\n\n"
            "Я помогу тебе:\n"
            "• Рассчитать оптимальную калорийность\n"
            "• Составить персональный рацион на день\n"
            "• Учесть твои пищевые предпочтения и ограничения\n\n"
            "Готов начать?",
            reply_markup=start_kb(),
        )
