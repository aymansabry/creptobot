# core/bot.py

from aiogram import Bot, Dispatcher
from config.config import Config

bot = Bot(token=Config.BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)
