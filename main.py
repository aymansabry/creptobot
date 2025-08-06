import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from config import config
from handlers import routers

async def main():
    # إعداد البوت والتخزين
    bot = Bot(token=config.BOT_TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher(storage=MemoryStorage())
    
    # تسجيل جميع الراوترات
    for router in routers:
        dp.include_router(router)

    try:
        print(f"🚀 Starting bot on port {config.PORT}")
        
        if config.DEPLOY_MODE == "webhook":
            from aiogram.webhook.aiohttp_server import setup_application
            from aiohttp import web
            
            # تنظيف أي تحديثات معلقة
            await bot.delete_webhook(drop_pending_updates=True)
            
            app = web.Application()
            setup_application(app, dp)
            
            # إعداد Webhook
            await bot.set_webhook(
                url=f"{config.WEBHOOK_URL}/webhook",
                drop_pending_updates=True
            )
            
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, host="0.0.0.0", port=config.PORT)
            await site.start()
            
            print(f"🌐 Webhook active at {config.WEBHOOK_URL}")
            await asyncio.Event().wait()  # تشغيل بدون نهاية
            
        else:
            print("🔄 Starting in polling mode...")
            await bot.delete_webhook(drop_pending_updates=True)
            await dp.start_polling(bot, 
                                allowed_updates=dp.resolve_used_update_types(),
                                close_bot_session=True)

    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        if not bot.is_closed():
            await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
