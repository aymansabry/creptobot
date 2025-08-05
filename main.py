import logging
from aiogram import Bot, Dispatcher
from config.settings import settings
from handlers import user_handlers, admin_handlers, trade_handlers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

async def main():
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher()
    
    # Register handlers
    user_handlers.register_handlers(dp)
    admin_handlers.register_handlers(dp)
    trade_handlers.register_handlers(dp)
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
