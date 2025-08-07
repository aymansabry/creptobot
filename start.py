import asyncio
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from logger import logger
from handlers import start, admin_panel, user_dashboard, auto_invest, manual_invest, withdraw, support, stats
from database.db import init_db

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # ربط قواعد البيانات
    await init_db()

    # تسجيل الهاندلرز
    dp.include_routers(
        start.router,
        user_dashboard.router,
        auto_invest.router,
        manual_invest.router,
        withdraw.router,
        support.router,
        admin_panel.router,
        stats.router
    )

    logger.info("🚀 Bot Started!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
