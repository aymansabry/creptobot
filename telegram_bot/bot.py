import asyncio
from aiogram import Bot, Dispatcher, Router
from core.config import TELEGRAM_BOT_TOKEN
from telegram_bot.handlers import setup_handlers
from aiogram.fsm.storage.memory import MemoryStorage

storage = MemoryStorage()

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher(storage=storage)
router = Router()

setup_handlers(router)
dp.include_router(router)
