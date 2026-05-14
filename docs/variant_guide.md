# Техническое руководство: Telegram-бот FitBot на GigaChat (LLM)

## Введение

В данном руководстве описан процесс создания Telegram-бота **FitBot** с нуля. Бот использует большую языковую модель **GigaChat** от Сбер для генерации персонального рациона питания, утренней зарядки и подбора блюд из продуктов холодильника.

**Стек технологий:**
- Python 3.11+
- aiogram 3 — фреймворк для Telegram-ботов
- GigaChat API — российская LLM от Сбер
- aiosqlite — асинхронная база данных SQLite
- APScheduler — планировщик задач

---

## 1. Подготовка окружения

### 1.1 Установка Python

Скачайте Python 3.11 или новее с официального сайта: https://www.python.org/downloads/

Проверьте установку:
```bash
python --version
```

### 1.2 Создание виртуального окружения

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux / macOS
source venv/bin/activate
```

### 1.3 Установка зависимостей

```bash
pip install aiogram==3.17.0 gigachat python-dotenv aiosqlite apscheduler pytz
```

Или через файл зависимостей:
```bash
pip install -r requirements.txt
```

Содержимое `requirements.txt`:
```
aiogram==3.17.0
gigachat>=0.1.28
python-dotenv>=1.0.0
aiosqlite>=0.20.0
apscheduler>=3.10.0
pytz>=2024.1
```

---

## 2. Получение токенов доступа

### 2.1 Токен Telegram-бота

1. Откройте Telegram, найдите [@BotFather](https://t.me/BotFather).
2. Отправьте команду `/newbot`.
3. Придумайте имя и username бота.
4. Скопируйте полученный токен — он выглядит так: `1234567890:AABBccdd...`

### 2.2 Credentials GigaChat

1. Зарегистрируйтесь на [developers.sber.ru](https://developers.sber.ru/portal/products/gigachat).
2. Создайте приложение и получите **Client ID** и **Client Secret**.
3. Закодируйте их в Base64: `base64(ClientID:ClientSecret)` — это и есть `GIGACHAT_CREDENTIALS`.

### 2.3 Файл .env

Создайте файл `.env` в корне проекта:
```
BOT_TOKEN=ваш_токен_от_BotFather
GIGACHAT_CREDENTIALS=ваши_credentials_в_base64
```

> **Важно:** добавьте `.env` в `.gitignore`, чтобы не публиковать секреты!

---

## 3. Структура проекта

```
fitbot/
├── bot.py                  # точка входа
├── config.py               # загрузка переменных окружения
├── scheduler.py            # утренняя рассылка
├── requirements.txt
├── .env                    # секреты (не коммитить!)
├── .env.example            # шаблон для команды
├── handlers/
│   ├── __init__.py
│   ├── start.py            # обработчик /start
│   ├── diet.py             # сбор профиля и генерация рациона
│   └── fridge.py           # блюда из холодильника
├── services/
│   ├── __init__.py
│   ├── ai_service.py       # запросы к GigaChat API
│   └── calorie_calc.py     # расчёт калорий по формуле Миффлина
├── keyboards/
│   ├── __init__.py
│   └── diet_kb.py          # inline-клавиатуры
├── states/
│   ├── __init__.py
│   └── user_states.py      # FSM-состояния
└── database/
    ├── __init__.py
    └── db.py               # работа с SQLite
```

---

## 4. Архитектура бота

```
Пользователь
    │
    ▼ /start
┌─────────────┐
│  handlers/  │  ← aiogram Router принимает сообщения
│  start.py   │
└──────┬──────┘
       │ новый пользователь → FSM-диалог
       ▼
┌─────────────┐
│  handlers/  │  ← пошагово собирает параметры (имя, вес, рост...)
│  diet.py    │
└──────┬──────┘
       │ все параметры собраны
       ▼
┌──────────────┐     ┌─────────────────┐
│  calorie_    │ ──► │   GigaChat API  │
│  calc.py     │     │  (LLM-модель)   │
└──────────────┘     └────────┬────────┘
                              │ сгенерированный текст рациона
                              ▼
                     Telegram-сообщение пользователю
```

**FSM (Finite State Machine)** — конечный автомат для управления диалогом. Каждый шаг диалога — это отдельное состояние. Пользователь не может пропустить шаг.

---

## 5. Пошаговая реализация

### Шаг 1: Точка входа (bot.py)

```python
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from handlers import start, diet, fridge
from database.db import init_db
from scheduler import setup_scheduler

async def main():
    await init_db()                        # создаём таблицы в БД
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())  # FSM хранится в памяти
    dp.include_router(start.router)
    dp.include_router(diet.router)
    dp.include_router(fridge.router)
    scheduler = setup_scheduler(bot)       # утренняя рассылка
    scheduler.start()
    await dp.start_polling(bot)            # запускаем бота

asyncio.run(main())
```

### Шаг 2: Загрузка конфигурации (config.py)

```python
import os
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
GIGACHAT_CREDENTIALS: str = os.getenv("GIGACHAT_CREDENTIALS", "")
```

### Шаг 3: FSM-состояния (states/user_states.py)

```python
from aiogram.fsm.state import State, StatesGroup

class ProfileStates(StatesGroup):
    name        = State()
    gender      = State()
    age         = State()
    height      = State()
    weight      = State()
    goal        = State()
    activity    = State()
    restrictions = State()
    preferences = State()

class FridgeStates(StatesGroup):
    waiting_products = State()
```

### Шаг 4: База данных (database/db.py)

Используем SQLite через `aiosqlite` для асинхронной работы. Таблица `users` хранит профиль каждого пользователя:

```python
import aiosqlite

DB_PATH = "fitbot.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                name TEXT, gender TEXT, age INTEGER,
                height INTEGER, weight REAL,
                goal TEXT, activity TEXT,
                restrictions TEXT DEFAULT 'none',
                preferences TEXT DEFAULT 'none',
                target_calories INTEGER,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()
```

### Шаг 5: Расчёт калорий (services/calorie_calc.py)

Используем формулу Миффлина-Сен Жеора для базового метаболизма (BMR):

```
Мужчины: BMR = 10×вес + 6.25×рост − 5×возраст + 5
Женщины: BMR = 10×вес + 6.25×рост − 5×возраст − 161
```

Затем умножаем BMR на коэффициент активности (TDEE) и вычитаем дефицит калорий:

```python
def calc_target_calories(weight, height, age, gender, activity, goal):
    bmr = 10*weight + 6.25*height - 5*age + (5 if gender == "male" else -161)
    activity_coeff = {"low": 1.2, "medium": 1.375, "high": 1.55}
    goal_deficit = {"-2": 500, "-5": 700, "-10": 900, "-15": 1000}
    tdee = bmr * activity_coeff[activity]
    return max(1200, round(tdee - goal_deficit[goal]))
```

### Шаг 6: Запросы к GigaChat (services/ai_service.py)

```python
from gigachat import GigaChatAsyncClient, Chat, Messages, MessagesRole
from config import GIGACHAT_CREDENTIALS

async def _call_giga(prompt: str, temperature: float = 0.9) -> str:
    async with GigaChatAsyncClient(
        credentials=GIGACHAT_CREDENTIALS,
        verify_ssl_certs=False
    ) as giga:
        response = await giga.achat(Chat(
            messages=[Messages(role=MessagesRole.USER, content=prompt)],
            temperature=temperature,
        ))
    return response.choices[0].message.content
```

**Ключевые параметры:**
- `temperature` — «творческость» модели (0.0 = детерминированно, 1.0 = максимально разнообразно).
- `verify_ssl_certs=False` — необходимо для работы с GigaChat на Windows.

### Шаг 7: Планировщик утренних сообщений (scheduler.py)

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

def setup_scheduler(bot):
    scheduler = AsyncIOScheduler(timezone=pytz.timezone("Europe/Moscow"))
    scheduler.add_job(
        send_morning_messages,
        trigger=CronTrigger(hour=9, minute=0),
        args=[bot],
    )
    return scheduler
```

---

## 6. Промпт-инжиниринг

Качество ответа LLM полностью зависит от промпта. Мы использовали несколько приёмов:

| Приём | Пример применения |
|-------|------------------|
| **Role prompting** | «Ты профессиональный диетолог» |
| **Структурированный ввод** | Параметры пользователя в виде списка |
| **Явные ограничения формата** | «Не используй markdown, используй эмодзи» |
| **Few-shot** | Указание конкретного формата вывода |

---

## 7. Запуск бота

```bash
# Активируйте виртуальное окружение
venv\Scripts\activate  # Windows

# Запустите бота
python bot.py
```

Бот начнёт принимать сообщения. Откройте Telegram, найдите вашего бота и отправьте `/start`.

---

## 8. Модификации и улучшения

В ходе разработки были реализованы следующие улучшения сверх базовой реализации:

1. **Функция «Холодильник»** — пользователь перечисляет продукты, бот генерирует 3 рецепта.
2. **Утренняя рассылка** — автоматическая отправка зарядки и рациона каждое утро в 09:00 МСК.
3. **Обработка лимитов API** — при ошибке 429 бот делает паузу и повторяет запрос (retry с exponential backoff).
4. **Хранение профиля** — повторные пользователи не вводят данные заново, бот помнит их через SQLite.
5. **Персонализированное приветствие** — особое сообщение для близких пользователя (пасхальное яйцо).
