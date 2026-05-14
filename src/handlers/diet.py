from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from states.user_states import ProfileStates
from keyboards.diet_kb import gender_kb, goal_kb, activity_kb, skip_kb, diet_actions_kb
from services.calorie_calc import calc_target_calories
from services.ai_service import generate_diet
from database.db import save_user, get_user

router = Router()


@router.callback_query(F.data == "start_profile")
async def cb_start_profile(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Как тебя зовут?")
    await state.set_state(ProfileStates.name)
    await callback.answer()


@router.message(ProfileStates.name)
async def process_name(message: Message, state: FSMContext):
    name = message.text.strip()
    await state.update_data(name=name)
    await message.answer(f"Приятно познакомиться, {name}! Укажи свой пол:", reply_markup=gender_kb())
    await state.set_state(ProfileStates.gender)


@router.callback_query(ProfileStates.gender, F.data.startswith("gender:"))
async def process_gender(callback: CallbackQuery, state: FSMContext):
    gender = callback.data.split(":")[1]
    await state.update_data(gender=gender)
    await callback.message.answer("Сколько тебе лет?")
    await state.set_state(ProfileStates.age)
    await callback.answer()


@router.message(ProfileStates.age)
async def process_age(message: Message, state: FSMContext):
    if not message.text.isdigit() or not (10 <= int(message.text) <= 100):
        await message.answer("Пожалуйста, введи корректный возраст (от 10 до 100):")
        return
    await state.update_data(age=int(message.text))
    await message.answer("Какой у тебя рост? (в сантиметрах)")
    await state.set_state(ProfileStates.height)


@router.message(ProfileStates.height)
async def process_height(message: Message, state: FSMContext):
    if not message.text.isdigit() or not (100 <= int(message.text) <= 250):
        await message.answer("Пожалуйста, введи корректный рост в см (от 100 до 250):")
        return
    await state.update_data(height=int(message.text))
    await message.answer("Какой у тебя вес? (в килограммах)")
    await state.set_state(ProfileStates.weight)


@router.message(ProfileStates.weight)
async def process_weight(message: Message, state: FSMContext):
    try:
        weight = float(message.text.replace(",", "."))
        if not (30 <= weight <= 300):
            raise ValueError
    except ValueError:
        await message.answer("Пожалуйста, введи корректный вес в кг (от 30 до 300):")
        return
    await state.update_data(weight=weight)
    await message.answer("Сколько килограммов ты хочешь сбросить?", reply_markup=goal_kb())
    await state.set_state(ProfileStates.goal)


@router.callback_query(ProfileStates.goal, F.data.startswith("goal:"))
async def process_goal(callback: CallbackQuery, state: FSMContext):
    goal = callback.data.split(":")[1]
    await state.update_data(goal=goal)
    await callback.message.answer("Как ты оцениваешь свою физическую активность?", reply_markup=activity_kb())
    await state.set_state(ProfileStates.activity)
    await callback.answer()


@router.callback_query(ProfileStates.activity, F.data.startswith("activity:"))
async def process_activity(callback: CallbackQuery, state: FSMContext):
    activity = callback.data.split(":")[1]
    await state.update_data(activity=activity)
    await callback.message.answer(
        "Есть ли у тебя пищевые ограничения или аллергии?\n"
        "(например: без глютена, аллергия на орехи, не ем мясо)\n\n"
        "Или нажми кнопку, если ограничений нет:",
        reply_markup=skip_kb("skip:restrictions"),
    )
    await state.set_state(ProfileStates.restrictions)
    await callback.answer()


@router.message(ProfileStates.restrictions)
async def process_restrictions(message: Message, state: FSMContext):
    await state.update_data(restrictions=message.text.strip())
    await _ask_preferences(message, state)


@router.callback_query(ProfileStates.restrictions, F.data == "skip:restrictions")
async def skip_restrictions(callback: CallbackQuery, state: FSMContext):
    await state.update_data(restrictions="none")
    await _ask_preferences(callback.message, state)
    await callback.answer()


async def _ask_preferences(message: Message, state: FSMContext):
    await message.answer(
        "Какие продукты или блюда ты предпочитаешь?\n"
        "(например: люблю курицу и овощи, не люблю рыбу)\n\n"
        "Или нажми кнопку, если без предпочтений:",
        reply_markup=skip_kb("skip:preferences"),
    )
    await state.set_state(ProfileStates.preferences)


@router.message(ProfileStates.preferences)
async def process_preferences(message: Message, state: FSMContext):
    await state.update_data(preferences=message.text.strip())
    await _generate_and_send(message, state)


@router.callback_query(ProfileStates.preferences, F.data == "skip:preferences")
async def skip_preferences(callback: CallbackQuery, state: FSMContext):
    await state.update_data(preferences="none")
    await _generate_and_send(callback.message, state, user_id=callback.from_user.id)
    await callback.answer()


async def _generate_and_send(message: Message, state: FSMContext, user_id: int = None, alternative: bool = False):
    data = await state.get_data()
    uid = user_id or message.chat.id

    target_calories = calc_target_calories(
        weight=data["weight"],
        height=data["height"],
        age=data["age"],
        gender=data["gender"],
        activity=data["activity"],
        goal=data["goal"],
    )

    profile = {**data, "target_calories": target_calories}
    await save_user(uid, profile)

    thinking_msg = await message.answer("Составляю твой персональный рацион... Это займёт несколько секунд.")

    try:
        diet_text = await generate_diet(profile, target_calories, alternative=alternative)
    except Exception:
        await thinking_msg.delete()
        await message.answer(
            "Упс, сервис сейчас немного перегружен 😔\n"
            "Попробуй нажать кнопку ещё раз через минуту.",
            reply_markup=diet_actions_kb(),
        )
        return

    await thinking_msg.delete()
    await message.answer(
        f"Твой рацион на день ({target_calories} ккал):\n\n{diet_text}",
        reply_markup=diet_actions_kb(),
    )
    await state.clear()


@router.callback_query(F.data == "diet:generate_existing")
async def cb_generate_existing(callback: CallbackQuery, state: FSMContext):
    uid = callback.from_user.id
    profile = await get_user(uid)
    if not profile:
        await callback.message.answer("Профиль не найден. Пожалуйста, начни заново с /start.")
        await callback.answer()
        return
    await state.set_data(profile)
    await _generate_and_send(callback.message, state, user_id=uid)
    await callback.answer()


@router.callback_query(F.data == "diet:alternative")
async def cb_alternative(callback: CallbackQuery, state: FSMContext):
    uid = callback.from_user.id
    profile = await get_user(uid)
    if not profile:
        await callback.message.answer("Профиль не найден. Пожалуйста, начни заново с /start.")
        await callback.answer()
        return
    await state.set_data(profile)
    await callback.message.answer("Генерирую другой вариант рациона...")
    await _generate_and_send(callback.message, state, user_id=uid, alternative=True)
    await callback.answer()


@router.callback_query(F.data == "diet:restart")
async def cb_restart(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    from keyboards.diet_kb import start_kb
    await callback.message.answer(
        "Хорошо, начнём заново! Нажми кнопку для старта:",
        reply_markup=start_kb(),
    )
    await callback.answer()
