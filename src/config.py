import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
GIGACHAT_CREDENTIALS: str = os.getenv("GIGACHAT_CREDENTIALS", "")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан в .env")
if not GIGACHAT_CREDENTIALS:
    raise ValueError("GIGACHAT_CREDENTIALS не задан в .env")
