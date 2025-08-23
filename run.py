import asyncio
from bot import main as bot_main  # استدعاء دالة main من bot.py

if __name__ == "__main__":
    # تشغيل البوت
    asyncio.run(bot_main())
