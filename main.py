import os
from aiogram import Bot, Dispatcher
from config import config

try:
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher(bot)
    
    async def on_startup():
        print("✅ تم تهيئة البوت بنجاح!")
        if not config.TRONGRID_API_KEY:
            print("⚠️ تحذير: TRONGRID_API_KEY غير معرّف - سيتم تعطيل ميزات TRON")

except Exception as e:
    print(f"❌ خطأ في التهيئة: {str(e)}")
    raise
