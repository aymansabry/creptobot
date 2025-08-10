import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from database import create_tables, SessionLocal
from settings import BOT_TOKEN, OWNER_ID

# إنشاء الجداول قبل بدء البوت
create_tables()

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# تعريف أدوار (هذه مجرد أمثلة، يمكنك تحديثها حسب قاعدة البيانات)
ADMINS = {int(OWNER_ID)}  # مالك البوت
MANAGERS = set()          # أضف معرفات المدراء هنا
CLIENTS = set()           # أضف معرفات العملاء هنا أو أضفهم تلقائياً عند استخدام البوت

# قوائم لوحة المفاتيح
owner_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="إدارة المدراء")],
        [KeyboardButton(text="إدارة العملاء")],
        [KeyboardButton(text="تقارير")],
        [KeyboardButton(text="إعدادات")]
    ],
    resize_keyboard=True
)

manager_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="مراجعة العمليات")],
        [KeyboardButton(text="تقارير")]
    ],
    resize_keyboard=True
)

client_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="إضافة API")],
        [KeyboardButton(text="الرصيد")],
        [KeyboardButton(text="بدء المراجحة")]
    ],
    resize_keyboard=True
)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    await message.reply("أهلاً! البوت يعمل بنجاح.")
    # إرسال القائمة المناسبة بناءً على الدور
    if user_id in ADMINS:
        await message.answer("مرحباً مالك البوت", reply_markup=owner_kb)
    elif user_id in MANAGERS:
        await message.answer("مرحباً مدير", reply_markup=manager_kb)
    else:
        # يعتبر عميل بشكل افتراضي
        CLIENTS.add(user_id)
        await message.answer("مرحباً عميل", reply_markup=client_kb)

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.reply("هذه أوامر البوت المتاحة:\n/start\n/help\n/menu")

@dp.message(Command("menu"))
async def cmd_menu(message: types.Message):
    user_id = message.from_user.id
    if user_id in ADMINS:
        await message.answer("قائمة مالك البوت", reply_markup=owner_kb)
    elif user_id in MANAGERS:
        await message.answer("قائمة المدير", reply_markup=manager_kb)
    elif user_id in CLIENTS:
        await message.answer("قائمة العميل", reply_markup=client_kb)
    else:
        await message.answer("عذراً، لا تملك صلاحيات في النظام.")

@dp.message()
async def handle_buttons(message: types.Message):
    text = message.text
    user_id = message.from_user.id

    if user_id in ADMINS:
        if text == "إدارة المدراء":
            await message.reply("هنا يمكنك إدارة المدراء.")
        elif text == "إدارة العملاء":
            await message.reply("هنا يمكنك إدارة العملاء.")
        elif text == "تقارير":
            await message.reply("عرض التقارير.")
        elif text == "إعدادات":
            await message.reply("صفحة الإعدادات.")
        else:
            await message.reply("اختيار غير معروف في قائمة المالك.")
    elif user_id in MANAGERS:
        if text == "مراجعة العمليات":
            await message.reply("عرض العمليات الجارية.")
        elif text == "تقارير":
            await message.reply("عرض التقارير.")
        else:
            await message.reply("اختيار غير معروف في قائمة المدير.")
    elif user_id in CLIENTS:
        if text == "إضافة API":
            await message.reply("أرسل مفاتيح API الخاصة بك.")
        elif text == "الرصيد":
            await message.reply("عرض رصيدك الحالي.")
        elif text == "بدء المراجحة":
            await message.reply("تم بدء المراجحة الخاصة بك.")
        else:
            await message.reply("اختيار غير معروف في قائمة العميل.")
    else:
        await message.reply("عذراً، لا تملك صلاحيات في النظام.")

async def main():
    print("البوت بدأ العمل")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())