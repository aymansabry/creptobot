import os
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from config import config
from handlers import admin_router, commands_router, deals_router

async def main():
    # إعداد البوت مع تخزين الحالة
    bot = Bot(token=config.BOT_TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher(storage=MemoryStorage())
    
    # تسجيل الراوترات
    dp.include_router(commands_router)
    dp.include_router(admin_router)
    dp.include_router(deals_router)

    try:
        print(f"🚀 Starting bot instance (PORT: {config.PORT})")
        
        if config.is_production:
            from aiogram.webhook.aiohttp_server import setup_application
            from aiohttp import web
            
            # إيقاف أي تحديثات معلقة وتنظيف الجلسات
            await bot.delete_webhook(drop_pending_updates=True)
            await bot.session.close()
            
            app = web.Application()
            setup_application(app, dp)
            
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, host="0.0.0.0", port=config.PORT)
            await site.start()
            
            print(f"🌐 Webhook active at {config.WEBHOOK_URL}")
            await bot.set_webhook(
                url=f"{config.WEBHOOK_URL}/webhook",
                drop_pending_updates=True
            )
            
            await asyncio.Event().wait()  # التشغيل المستمر
        else:
            print("🔄 Starting in polling mode...")
            # تنظيف كامل قبل البدء
            await bot.delete_webhook(drop_pending_updates=True)
            await bot.session.close()
            
            # تشغيل البوت مع إعدادات مضبوطة
            await dp.start_polling(
                bot,
                allowed_updates=dp.resolve_used_update_types(),
                close_bot_session=True
            )
            
    except Exception as e:
        print(f"❌ Critical error: {e}")
    finally:
        if not bot.is_closed():
            await bot.session.close()
        print("🛑 Bot stopped successfully")

if __name__ == "__main__":
    asyncio.run(main())
