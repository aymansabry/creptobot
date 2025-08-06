import asyncio
from aiogram import Bot, Dispatcher
from config import config
from handlers.buttons import deals, wallet

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(bot)

# تسجيل handlers
dp.register_message_handler(wallet.create_wallet, text="💰 إنشاء محفظة")
dp.register_callback_query_handler(deals.handle_real_deal, text_startswith="deal_")

async def main():
    if config.BINANCE_API_URL == "https://testnet.binance.vision":
        print("⚠️ يعمل البوت في وضع الاختبار")
    await dp.start_polling()

if __name__ == "__main__":
    asyncio.run(main())
