import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from handlers import start, diet
from handlers import fridge
from database.db import init_db
from scheduler import setup_scheduler

logging.basicConfig(level=logging.INFO)


async def main():
    await init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(start.router)
    dp.include_router(diet.router)
    dp.include_router(fridge.router)

    scheduler = setup_scheduler(bot)
    scheduler.start()
    logging.info("Планировщик запущен — рассылка в 09:00 МСК")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
