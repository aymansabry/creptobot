from aiogram import Dispatcher, types

async def show_trading_menu(message: types.Message):
    await message.answer("قائمة التداول:")

def register_handlers(dp: Dispatcher):
    dp.register_message_handler(show_trading_menu, commands=["trade"], state="*")
