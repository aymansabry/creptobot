from aiogram import Bot, Dispatcher, executor, types
from settings import BOT_TOKEN
from handlers import start, button_handler

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# تسجيل الهاندلرز
dp.register_message_handler(start, commands=["start"])
dp.register_callback_query_handler(button_handler)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)