from gigachat import GigaChatAsyncClient
from gigachat import Chat, Messages, MessagesRole
from config import GIGACHAT_CREDENTIALS
from services.calorie_calc import GOAL_LABELS, ACTIVITY_LABELS


def _build_prompt(profile: dict, target_calories: int, alternative: bool = False) -> str:
    restriction_text = profile["restrictions"] if profile["restrictions"] != "none" else "нет"
    preference_text = profile["preferences"] if profile["preferences"] != "none" else "нет"
    goal_label = GOAL_LABELS[profile["goal"]]
    activity_label = ACTIVITY_LABELS[profile["activity"]]
    gender_label = "мужчина" if profile["gender"] == "male" else "женщина"

    alternative_note = " Предложи другой набор блюд, полностью отличный от предыдущего варианта." if alternative else ""

    return (
        f"Ты профессиональный диетолог. Составь подробный рацион питания на один день.{alternative_note}\n\n"
        f"Данные о пользователе:\n"
        f"- Имя: {profile['name']}\n"
        f"- Пол: {gender_label}\n"
        f"- Возраст: {profile['age']} лет\n"
        f"- Рост: {profile['height']} см\n"
        f"- Вес: {profile['weight']} кг\n"
        f"- Цель: похудеть на {goal_label}\n"
        f"- Уровень активности: {activity_label}\n"
        f"- Пищевые ограничения/аллергии: {restriction_text}\n"
        f"- Предпочтения в еде: {preference_text}\n"
        f"- Целевые калории в день: {target_calories} ккал\n\n"
        f"Составь рацион из 5 приёмов пищи: завтрак, перекус, обед, перекус, ужин.\n\n"
        f"ВАЖНО — форматирование ответа:\n"
        f"- Не используй markdown: никаких #, ##, ###, **, *, ---, _\n"
        f"- Используй эмодзи для оформления\n"
        f"- Каждый приём пищи начинай с эмодзи и названия, например: 🌅 ЗАВТРАК\n"
        f"- Для каждого приёма пищи укажи: блюдо, состав с граммовкой, калорийность, совет по приготовлению\n"
        f"- В конце напиши итоговые калории за день в формате: 📊 Итого за день: X ккал\n"
        f"- Заверши коротким мотивационным сообщением с эмодзи для {profile['name']}\n"
    )


async def _call_giga(prompt: str, temperature: float = 0.9) -> str:
    import asyncio
    from gigachat.exceptions import GigaChatException

    delays = [5, 15, 30]
    for delay in delays + [None]:
        try:
            async with GigaChatAsyncClient(credentials=GIGACHAT_CREDENTIALS, verify_ssl_certs=False) as giga:
                response = await giga.achat(
                    Chat(
                        messages=[Messages(role=MessagesRole.USER, content=prompt)],
                        temperature=temperature,
                    )
                )
            return response.choices[0].message.content
        except GigaChatException as e:
            if "429" in str(e) and delay is not None:
                await asyncio.sleep(delay)
                continue
            raise


async def generate_diet(profile: dict, target_calories: int, alternative: bool = False) -> str:
    prompt = _build_prompt(profile, target_calories, alternative)
    return await _call_giga(prompt, temperature=1.0 if alternative else 0.8)


async def generate_morning(profile: dict, target_calories: int) -> tuple[str, str]:
    gender_label = "мужчина" if profile["gender"] == "male" else "женщина"
    activity_label = ACTIVITY_LABELS[profile["activity"]]

    workout_prompt = (
        f"Ты персональный тренер. Придумай утреннюю зарядку на сегодня для человека.\n\n"
        f"Данные: пол — {gender_label}, возраст — {profile['age']} лет, "
        f"активность — {activity_label}.\n\n"
        f"ВАЖНО — форматирование:\n"
        f"- Не используй markdown: никаких #, ##, **, *, ---\n"
        f"- Используй эмодзи\n"
        f"- Составь 5-6 упражнений с количеством повторений или временем\n"
        f"- Каждое упражнение с новой строки, начинай с эмодзи\n"
        f"- В конце короткая мотивационная фраза для {profile['name']}"
    )

    diet_prompt = _build_prompt(profile, target_calories, alternative=True)

    import asyncio
    workout_text = await _call_giga(workout_prompt, temperature=1.0)
    await asyncio.sleep(3)
    diet_text = await _call_giga(diet_prompt, temperature=1.0)
    return workout_text, diet_text


async def generate_fridge_dishes(products: str, profile: dict) -> str:
    restriction_text = profile.get("restrictions", "none")
    if restriction_text == "none":
        restriction_text = "нет"

    prompt = (
        f"Ты повар-диетолог. Пользователь хочет похудеть и у него есть следующие продукты: {products}.\n\n"
        f"Пищевые ограничения: {restriction_text}.\n\n"
        f"Предложи ровно 3 блюда которые можно приготовить из этих продуктов.\n\n"
        f"ВАЖНО — форматирование:\n"
        f"- Не используй markdown: никаких #, ##, **, *, ---\n"
        f"- Используй эмодзи\n"
        f"- Для каждого блюда укажи: название, состав с граммовкой, калорийность, "
        f"краткий рецепт (2-3 шага)\n"
        f"- Нумеруй блюда: 1️⃣, 2️⃣, 3️⃣\n"
        f"- Выбирай блюда подходящие для похудения"
    )
    return await _call_giga(prompt, temperature=0.9)
