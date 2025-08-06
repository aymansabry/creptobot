from aiogram import types, Dispatcher
from aiogram.types import CallbackQuery
from keyboards.user_keyboards import main_menu
from database.wallets import get_user_wallet
from utils.formatters import format_currency

async def start_command(message: types.Message):
    await message.answer("مرحبًا بك في بوت الاستثمار 🤖", reply_markup=main_menu())

async def my_wallet_callback(call: CallbackQuery):
    wallet = await get_user_wallet(call.from_user.id)
    if wallet:
        msg = f"💼 الرصيد الحالي: {format_currency(wallet['balance'])}"
    else:
        msg = "❌ لم يتم العثور على محفظتك"
    await call.message.answer(msg)

def register_user_handlers(dp: Dispatcher):
    dp.register_message_handler(start_command, commands=["start"])
    dp.register_callback_query_handler(my_wallet_callback, text="my_wallet")
