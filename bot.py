import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from database import create_tables, SessionLocal
from settings import BOT_TOKEN, OWNER_ID

# إنشاء الجداول قبل بدء البوت
create_tables()

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.reply("أهلاً! البوت يعمل بنجاح.")

@dp.message_handler(commands=['help'])
async def cmd_help(message: types.Message):
    await message.reply("هذه أوامر البوت المتاحة:\n/start\n/help")

# مثال على إضافة رسالة خاصة للمالك
@dp.message_handler(lambda message: message.from_user.id == int(OWNER_ID))
async def owner_only(message: types.Message):
    await message.reply("مرحباً مالك البوت!")

async def on_startup(dispatcher):
    print("البوت بدأ العمل")

async def on_shutdown(dispatcher):
    await bot.close()
    print("البوت توقف")

if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, on_shutdown=on_shutdown)