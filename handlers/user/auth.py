from aiogram import Dispatcher, types

async def start_command(message: types.Message):
    await message.answer("مرحباً بك في بوت التداول الذكي!")

def register_handlers(dp: Dispatcher):
    dp.register_message_handler(start_command, commands=["start"], state="*")
