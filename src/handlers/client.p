from aiogram import Dispatcher, types, F
from aiogram.filters import CommandStart
from src.services.investment import handle_auto_invest
from src.services.wallet import get_client_wallet_balance
from src.services.ai import suggest_deals
from src.keyboards.client_keyboards import main_menu_keyboard

async def start_handler(msg: types.Message):
    await msg.answer("مرحباً بك في بوت الاستثمار الذكي 🤖💰", reply_markup=main_menu_keyboard())

async def wallet_handler(msg: types.Message):
    balance = await get_client_wallet_balance(msg.from_user.id)
    await msg.answer(f"رصيدك الحالي: {balance} USDT")

async def invest_handler(msg: types.Message):
    await handle_auto_invest(msg)

async def deals_handler(msg: types.Message):
    deals = await suggest_deals()
    await msg.answer(f"الصفقات المتاحة:\n\n{deals}")

def register_client_handlers(dp: Dispatcher):
    dp.message.register(start_handler, CommandStart())
    dp.message.register(wallet_handler, F.text == "💼 محفظتي")
    dp.message.register(invest_handler, F.text == "🚀 استثمار تلقائي")
    dp.message.register(deals_handler, F.text == "📈 صفقات اليوم")
