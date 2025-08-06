import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from config import config
from handlers import commands

async def main():
    # إعداد البوت مع تخزين الحالة
    bot = Bot(token=config.BOT_TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(commands.router)

    try:
        print(f"🚀 Starting bot instance (PORT: {config.PORT})")
        
        if config.DEPLOY_MODE == "webhook":
            from aiogram.webhook.aiohttp_server import setup_application
            from aiohttp import web
            
            # إيقاف أي تحديثات معلقة
            await bot.delete_webhook(drop_pending_updates=True)
            
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
            
            await asyncio.Event().wait()
        else:
            print("🔄 Starting in polling mode...")
            await bot.delete_webhook()  # مهم لمنع التضارب
            await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
