import asyncio
import os
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from handlers import router
from db_migration import check_and_create_table  # استدعاء التهيئة

async def main():
    # تهيئة قاعدة البيانات
    await check_and_create_table()

    # إعداد البوت
    bot = Bot(token=os.getenv("BOT_TOKEN"))
    dp = Dispatcher()
    dp.include_router(router)

    # أوامر البوت الافتراضية
    await bot.set_my_commands([
        BotCommand(command="start", description="بدء التشغيل"),
        BotCommand(command="help", description="مساعدة")
    ])

    # بدء البوت
    await dp.start_polling(bot)

if __name__ == "__main__":
    import dotenv
    dotenv.load_dotenv()
    asyncio.run(main())
