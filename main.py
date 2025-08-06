import logging
from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from db.session import engine, Base
import time
from sqlalchemy import exc
from core.config import SystemConfig

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=SystemConfig.TELEGRAM_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

def initialize_db():
    retries = 5
    while retries > 0:
        try:
            Base.metadata.create_all(bind=engine)
            return True
        except exc.OperationalError as e:
            logging.error(f"Database connection failed: {e}")
            retries -= 1
            time.sleep(5)
    raise Exception("Failed to connect to database after multiple attempts")

async def on_startup(_):
    logging.info("Bot started successfully")

if __name__ == '__main__':
    # Initialize database first
    if initialize_db():
        # Import handlers after DB is ready
        from handlers import admin, user
        
        # Register handlers
        admin.register_handlers(dp)
        user.register_handlers(dp)
        
        # Start polling
        executor.start_polling(
            dp,
            skip_updates=True,
            on_startup=on_startup
        )
