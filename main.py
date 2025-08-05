import logging
from aiogram import Bot, Dispatcher, executor
from config.simple_settings import settings

# إعدادات التسجيل
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# تهيئة البوت
bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher(bot)

async def on_startup(_):
    """وظيفة تنفيذية عند بدء التشغيل"""
    logger.info("تم بدء تشغيل البوت بنجاح")
    logger.info(f"إصدار البوت: {await bot.get_me()}")

@dp.message_handler(commands=['start'])
async def start_command(message):
    """معالج أمر /start"""
    await message.reply("🟢 البوت يعمل بشكل طبيعي")

if __name__ == "__main__":
    try:
        logger.info("جاري بدء عملية polling...")
        executor.start_polling(
            dp,
            skip_updates=True,
            on_startup=on_startup,
            timeout=60
        )
    except Exception as e:
        logger.critical(f"حدث خطأ جسيم: {str(e)}")
