import logging
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher.filters import Command
from config.settings import settings
import asyncio

# Initialize logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Verify environment variables
def verify_settings():
    required_vars = {
        'BOT_TOKEN': settings.BOT_TOKEN,
        'DATABASE_URL': settings.DATABASE_URL,
        'ADMIN_IDS': settings.ADMIN_IDS,
        'BINANCE_API_KEY': settings.BINANCE_API_KEY,
        'BINANCE_SECRET_KEY': settings.BINANCE_SECRET_KEY,
        'AI_API_KEY': settings.AI_API_KEY
    }
    
    for name, value in required_vars.items():
        if not value:
            logger.error(f"Missing required environment variable: {name}")
            raise ValueError(f"{name} is required")
    
    logger.info("All environment variables are properly set")

# Initialize bot and dispatcher
bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher(bot)

# Register handlers
@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    await message.answer("🚀 Welcome to the Arbitrage Bot!")
    logger.info(f"New user started: {message.from_user.id}")

@dp.message_handler(commands=['admin'])
async def admin_handler(message: types.Message):
    if message.from_user.id not in settings.ADMIN_IDS:
        await message.answer("⛔ You are not authorized!")
        return
    
    await message.answer("🛠️ Admin panel activated")
    logger.info(f"Admin access: {message.from_user.id}")

async def main():
    try:
        verify_settings()
        logger.info("Starting bot polling...")
        await dp.start_polling()
    except Exception as e:
        logger.error(f"Bot failed: {str(e)}")
    finally:
        await bot.close()

if __name__ == "__main__":
    logger.info(f"Loaded settings: {settings}")
    asyncio.run(main())
