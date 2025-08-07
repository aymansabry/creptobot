import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from config import BOT_TOKEN
from handlers import (
    client_router,
    admin_router,
    invest_router,
    support_router,
    wallet_router
)

async def main():
    bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher()

    dp.include_router(client_router)
    dp.include_router(invest_router)
    dp.include_router(admin_router)
    dp.include_router(support_router)
    dp.include_router(wallet_router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
