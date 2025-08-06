import logging
from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from core.config import SystemConfig
from db.session import SessionLocal, Base, engine
from handlers import admin, user

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot
bot = Bot(token=SystemConfig.TELEGRAM_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Create database tables
Base.metadata.create_all(bind=engine)

# Register handlers
admin.register_handlers(dp)
user.register_handlers(dp)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
