import logging
from aiogram import Bot, Dispatcher, types
from config.settings import settings
import asyncio

# إعداد التسجيل
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def verify_settings():
    required_vars = {
        'BOT_TOKEN': settings.BOT_TOKEN,
        'DATABASE_URL': settings.DATABASE_URL,
        'BINANCE_API_KEY': settings.BINANCE_API_KEY,
        'BINANCE_SECRET_KEY': settings.BINANCE_SECRET_KEY,
        'AI_API_KEY': settings.AI_API_KEY
    }
    
    missing = [name for name, value in required_vars.items() if not value]
    if missing:
        raise ValueError(f"مفقود: {', '.join(missing)}")

try:
    verify_settings()
    logger.info("تم تحميل الإعدادات بنجاح")
    
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher(bot)

    @dp.message_handler(commands=['start'])
    async def start(message: types.Message):
        await message.answer("✅ البوت يعمل بشكل صحيح")

    async def main():
        await dp.start_polling()

    if __name__ == "__main__":
        asyncio.run(main())

except Exception as e:
    logger.critical(f"فشل التشغيل: {str(e)}")
    exit(1)
