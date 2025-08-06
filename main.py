import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from config import config
from handlers import commands

bot = Bot(token=config.BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

# تضمين الراوترات
dp.include_router(commands.router)

async def main():
    print(f"🚀 البوت يعمل على المنفذ {config.PORT}")
    
    if config.DEPLOY_MODE == "webhook":
        from aiogram.webhook.aiohttp_server import setup_application
        from aiohttp import web
        
        app = web.Application()
        setup_application(app, dp)
        
        await bot.set_webhook(
            url=f"{config.WEBHOOK_URL}/webhook",
            drop_pending_updates=True
        )
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host="0.0.0.0", port=config.PORT)
        await site.start()
        
        print(f"🌐 Webhook настроен на {config.WEBHOOK_URL}")
        await asyncio.Event().wait()
    else:
        print("🔄 بدء التشغيل في وضع Polling...")
        await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
