import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from database import Database, ExchangePlatform, User, ExchangeConnection
from config import Config
from datetime import datetime, timedelta
from typing import Dict, Any, List
import asyncio

# ... (بقية الimports والدوال تبقى كما هي)

async def set_bot_commands():
    """تعيين أوامر البوت"""
    commands = [
        types.BotCommand("start", "بدء استخدام البوت"),
        types.BotCommand("help", "مساعدة")
    ]
    await bot.set_my_commands(commands)

if __name__ == '__main__':
    from aiogram import executor
    
    # تنظيف أي عمليات معلقة
    loop = asyncio.get_event_loop()
    loop.run_until_complete(bot.delete_webhook(drop_pending_updates=True))
    loop.run_until_complete(set_bot_commands())
    
    try:
        executor.start_polling(
            dp,
            skip_updates=True,
            timeout=30,
            relax=0.5,
            on_startup=on_startup,
            on_shutdown=on_shutdown
        )
    except Exception as e:
        logger.critical(f"Failed to start bot: {e}")