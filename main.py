import os
import asyncio
from aiogram import Bot, Dispatcher
from config import config

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()

async def main():
    port = int(os.environ.get("PORT", 8000))  # الحصول على المنفذ من المتغيرات البيئية
    print(f"🚀 البوت يعمل على المنفذ {port}")
    
    # اختر بين وضعي التشغيل
    if config.DEPLOY_MODE == "webhook":
        from aiogram.webhook.aiohttp_server import setup_application
        from aiohttp import web
        
        app = web.Application()
        setup_application(app, dp)
        web.run_app(app, host="0.0.0.0", port=port)
    else:
        from aiogram import executor
        await executor.start_polling(dp, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
