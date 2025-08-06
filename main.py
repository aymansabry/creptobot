import os
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from config import config
from handlers.admin import router as admin_router
from handlers.commands import router as commands_router
from handlers.deals import router as deals_router

async def main():
    # إعداد البوت
    bot = Bot(token=config.BOT_TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher(storage=MemoryStorage())
    
    # تسجيل الراوترات
    dp.include_router(commands_router)
    dp.include_router(admin_router)
    dp.include_router(deals_router)

    try:
        print(f"🚀 البوت يعمل على المنفذ {config.PORT}")
        
        if config.is_production:
            from aiogram.webhook.aiohttp_server import setup_application
            from aiohttp import web
            
            await bot.delete_webhook(drop_pending_updates=True)
            
            app = web.Application()
            setup_application(app, dp)
            
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, host="0.0.0.0", port=config.PORT)
            await site.start()
            
            await bot.set_webhook(
                url=f"{config.WEBHOOK_URL}/webhook",
                drop_pending_updates=True
            )
            
            print(f"🌐 Webhook نشط على {config.WEBHOOK_URL}")
            await asyncio.Event().wait()
        else:
            print("🔄 بدء التشغيل في وضع Polling...")
            await bot.delete_webhook(drop_pending_updates=True)
            await dp.start_polling(bot)

    except Exception as e:
        print(f"❌ خطأ: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
