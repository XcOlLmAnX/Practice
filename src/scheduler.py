import asyncio
import logging

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from database.db import get_all_users
from services.ai_service import generate_morning

logger = logging.getLogger(__name__)
MOSCOW_TZ = pytz.timezone("Europe/Moscow")


async def send_morning_messages(bot) -> None:
    users = await get_all_users()
    if not users:
        return

    for user in users:
        try:
            workout_text, diet_text = await generate_morning(user, user["target_calories"])
            await bot.send_message(
                user["user_id"],
                f"☀️ Доброе утро, {user['name']}! Начинаем день правильно!\n\n"
                f"🏋️ УТРЕННЯЯ ЗАРЯДКА\n\n{workout_text}",
            )
            await asyncio.sleep(2)
            await bot.send_message(
                user["user_id"],
                f"🥗 РАЦИОН НА СЕГОДНЯ ({user['target_calories']} ккал)\n\n{diet_text}",
            )
            await asyncio.sleep(3)
        except Exception as e:
            logger.error(f"Ошибка при отправке утреннего сообщения пользователю {user['user_id']}: {e}")


def setup_scheduler(bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=MOSCOW_TZ)
    scheduler.add_job(
        send_morning_messages,
        trigger=CronTrigger(hour=9, minute=0, timezone=MOSCOW_TZ),
        args=[bot],
        id="morning_messages",
        replace_existing=True,
    )
    return scheduler
