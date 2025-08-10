import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from database import create_tables, SessionLocal
from settings import BOT_TOKEN, OWNER_ID

# إنشاء الجداول قبل بدء البوت
create_tables()

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()  # لا نمرر bot هنا

# قوائم المستخدمين
user_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/help"), KeyboardButton(text="/profile")],
    ],
    resize_keyboard=True
)

owner_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/help"), KeyboardButton(text="/admin_panel")],
        [KeyboardButton(text="/users"), KeyboardButton(text="/stats")]
    ],
    resize_keyboard=True
)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if message.from_user.id == int(OWNER_ID):
        await message.answer("أهلاً مالك البوت!", reply_markup=owner_keyboard)
    else:
        await message.answer("أهلاً! البوت يعمل بنجاح.", reply_markup=user_keyboard)

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.reply("هذه أوامر البوت المتاحة:\n/start\n/help\n/profile\n")

@dp.message(Command("profile"))
async def cmd_profile(message: types.Message):
    await message.reply(f"معلوماتك:\nمعرف التليجرام: {message.from_user.id}\nاسم المستخدم: {message.from_user.full_name}")

@dp.message(Command("admin_panel"))
async def cmd_admin_panel(message: types.Message):
    if message.from_user.id == int(OWNER_ID):
        await message.reply("لوحة تحكم المدير: هنا تضع أوامر الإدارة")
    else:
        await message.reply("غير مصرح لك باستخدام هذه الأوامر.")

@dp.message(Command("users"))
async def cmd_users(message: types.Message):
    if message.from_user.id == int(OWNER_ID):
        await message.reply("قائمة المستخدمين: ...")
    else:
        await message.reply("غير مصرح لك.")

@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    if message.from_user.id == int(OWNER_ID):
        await message.reply("إحصائيات البوت: ...")
    else:
        await message.reply("غير مصرح لك.")

async def main():
    print("البوت بدأ العمل")
    await dp.start_polling(bot)  # نمرر bot هنا فقط

if __name__ == '__main__':
    asyncio.run(main())