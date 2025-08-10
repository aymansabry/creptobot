import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from database import create_tables, SessionLocal
from settings import BOT_TOKEN, OWNER_ID

# إنشاء الجداول قبل بدء البوت
create_tables()

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command(commands=["start"]))
async def cmd_start(message: types.Message):
    await message.answer("أهلاً! البوت يعمل بنجاح.")

@dp.message(Command(commands=["help"]))
async def cmd_help(message: types.Message):
    await message.answer("هذه أوامر البوت المتاحة:\n/start\n/help")

@dp.message(lambda message: message.from_user.id == int(OWNER_ID))
async def owner_only(message: types.Message):
    await message.answer("مرحباً مالك البوت!")

async def main():
    # تسجيل البوت
    dp.include_router(dp)

    print("البوت بدأ العمل")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())