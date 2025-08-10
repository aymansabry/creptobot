import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from database import create_tables, SessionLocal
from settings import BOT_TOKEN, OWNER_ID

# إنشاء الجداول قبل بدء البوت
create_tables()

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.reply("أهلاً! البوت يعمل بنجاح.")

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.reply("هذه أوامر البوت المتاحة:\n/start\n/help")

# رسالة خاصة للمالك
@dp.message()
async def owner_only(message: types.Message):
    if message.from_user.id == int(OWNER_ID):
        await message.reply("مرحباً مالك البوت!")

async def main():
    print("البوت بدأ العمل")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())