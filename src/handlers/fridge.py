from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from states.user_states import FridgeStates
from services.ai_service import generate_fridge_dishes
from database.db import get_user

router = Router()


def _fridge_back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Попробовать другие блюда", callback_data="fridge:retry")],
        [InlineKeyboardButton(text="◀️ В меню", callback_data="fridge:menu")],
    ])


@router.message(Command("fridge"))
async def cmd_fridge(message: Message, state: FSMContext):
    await _ask_products(message, state)


@router.callback_query(F.data == "fridge:open")
async def cb_fridge_open(callback: CallbackQuery, state: FSMContext):
    await _ask_products(callback.message, state)
    await callback.answer()


async def _ask_products(message: Message, state: FSMContext):
    await message.answer(
        "🧊 Что есть в холодильнике?\n\n"
        "Перечисли продукты через запятую, и я предложу 3 блюда из них.\n\n"
        "Например: курица, яйца, помидоры, огурцы, сметана"
    )
    await state.set_state(FridgeStates.waiting_products)


@router.message(FridgeStates.waiting_products)
async def process_products(message: Message, state: FSMContext):
    products = message.text.strip()
    user = await get_user(message.from_user.id)

    thinking = await message.answer("Придумываю блюда из твоих продуктов... 🍳")
    try:
        result = await generate_fridge_dishes(products, user or {})
    except Exception:
        await thinking.delete()
        await message.answer(
            "Упс, сервис сейчас перегружен 😔\nПопробуй чуть позже.",
            reply_markup=_fridge_back_kb(),
        )
        await state.clear()
        return

    await thinking.delete()
    await message.answer(
        f"Вот что можно приготовить из твоих продуктов:\n\n{result}",
        reply_markup=_fridge_back_kb(),
    )
    await state.clear()


@router.callback_query(F.data == "fridge:retry")
async def cb_fridge_retry(callback: CallbackQuery, state: FSMContext):
    await _ask_products(callback.message, state)
    await callback.answer()


@router.callback_query(F.data == "fridge:menu")
async def cb_fridge_menu(callback: CallbackQuery, state: FSMContext):
    from database.db import get_user
    from keyboards.diet_kb import returning_user_kb, start_kb
    user = await get_user(callback.from_user.id)
    if user:
        await callback.message.answer(
            f"Главное меню, {user['name']} 👋",
            reply_markup=returning_user_kb(),
        )
    else:
        await callback.message.answer("Главное меню:", reply_markup=start_kb())
    await callback.answer()
