import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, Text
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from sqlalchemy.orm import Session
from database import create_tables, SessionLocal
from models import User, APIKey
from settings import BOT_TOKEN, OWNER_ID, FERNET_KEY
from cryptography.fernet import Fernet, InvalidToken

# إنشاء الجداول قبل بدء البوت
create_tables()

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

fernet = Fernet(FERNET_KEY.encode())

# حالة FSM لاستثمار المستخدم
class InvestmentStates(StatesGroup):
    waiting_for_investment_amount = State()

# وضع المدير أو المستخدم (تخزين مؤقت في الذاكرة)
admin_mode = {"is_admin_mode": True}

# لوحة مفاتيح المستخدم
user_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/help"), KeyboardButton(text="تسجيل/تعديل بيانات التداول")],
        [KeyboardButton(text="ابدأ استثمار"), KeyboardButton(text="استثمار وهمي")],
        [KeyboardButton(text="كشف حساب عن فترة"), KeyboardButton(text="حالة السوق")],
        [KeyboardButton(text="ايقاف الاستثمار")]
    ],
    resize_keyboard=True
)

# لوحة مفاتيح المدير
def get_owner_keyboard():
    buttons = [
        [KeyboardButton(text="/help"), KeyboardButton(text="/admin_panel")],
        [KeyboardButton(text="تعديل نسبة ربح البوت"), KeyboardButton(text="عدد المستخدمين")],
        [KeyboardButton(text="عدد المستخدمين أونلاين"), KeyboardButton(text="تقارير الاستثمار")],
        [KeyboardButton(text="حالة البوت البرمجية")]
    ]
    # الزر الخاص بالتبديل بين أوضاع المدير والمستخدم
    if admin_mode["is_admin_mode"]:
        buttons.append([KeyboardButton(text="استثمار حقيقي")])
    else:
        buttons.append([KeyboardButton(text="رجوع للوضع المدير")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if message.from_user.id == int(OWNER_ID):
        await message.answer("أهلاً مالك البوت!", reply_markup=get_owner_keyboard())
    else:
        await message.answer("أهلاً! البوت يعمل بنجاح.", reply_markup=user_keyboard)

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.reply(
        "هذه أوامر البوت المتاحة:\n"
        "/start\n"
        "/help\n"
        "تسجيل/تعديل بيانات التداول\n"
        "ابدأ استثمار\n"
        "استثمار وهمي\n"
        "كشف حساب عن فترة\n"
        "حالة السوق\n"
        "ايقاف الاستثمار\n"
    )

@dp.message(Text("استثمار حقيقي"))
async def switch_to_user_mode(message: types.Message):
    if message.from_user.id != int(OWNER_ID):
        await message.reply("غير مصرح لك.")
        return
    admin_mode["is_admin_mode"] = False
    await message.answer("تم التحويل لوضع مستخدم للاستثمار الحقيقي.", reply_markup=user_keyboard)

@dp.message(Text("رجوع للوضع المدير"))
async def switch_to_admin_mode(message: types.Message):
    if message.from_user.id != int(OWNER_ID):
        await message.reply("غير مصرح لك.")
        return
    admin_mode["is_admin_mode"] = True
    await message.answer("تم التحويل لوضع المدير.", reply_markup=get_owner_keyboard())

@dp.message(Text("ابدأ استثمار"))
async def start_investment(message: types.Message, state: FSMContext):
    # لو المرسل هو المدير في وضع مستخدم (استثمار حقيقي) أو مستخدم عادي
    if message.from_user.id == int(OWNER_ID) and not admin_mode["is_admin_mode"]:
        # يعمل كـ مستخدم عادي للاستثمار الحقيقي
        pass
    elif message.from_user.id == int(OWNER_ID) and admin_mode["is_admin_mode"]:
        await message.answer("يرجى التبديل لوضع الاستثمار الحقيقي عبر زر 'استثمار حقيقي' في لوحة المدير.")
        return
    # تحقق من تسجيل بيانات التداول
    with SessionLocal() as session:
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if not user:
            await message.answer("يجب تسجيل بيانات التداول أولاً عبر 'تسجيل/تعديل بيانات التداول'.")
            return
        if not getattr(user, "is_active", True):
            await message.answer("تم إيقاف الاستثمار الخاص بك، لا يمكنك البدء حالياً.")
            return

    await message.answer("أدخل مبلغ الاستثمار (مثلاً: 1000):", reply_markup=ReplyKeyboardRemove())
    await state.set_state(InvestmentStates.waiting_for_investment_amount)

@dp.message(state=InvestmentStates.waiting_for_investment_amount)
async def process_investment_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.strip())
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("يرجى إدخال مبلغ صحيح أكبر من صفر.")
        return

    with SessionLocal() as session:
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if not user:
            await message.answer("لم يتم العثور على بيانات المستخدم.")
            await state.clear()
            return

        # تحقق الرصيد (مبسط حاليا)
        user.investment_amount = amount
        user.is_active = True
        session.commit()

    await message.answer(f"تم تعيين مبلغ الاستثمار: {amount} بنجاح.\nيتم الآن بدء الاستثمار الآلي...")
    await state.clear()

    # هنا يمكنك إضافة منطق بدء الاستثمار الفعلي مع API المفاتيح
    # await run_investment_for_user(user)

@dp.message(Text("تسجيل/تعديل بيانات التداول"))
async def handle_api_key_entry(message: types.Message):
    await message.answer("ميزة تسجيل وتعديل بيانات التداول تحت التطوير.")

@dp.message(Command("admin_panel"))
async def cmd_admin_panel(message: types.Message):
    if message.from_user.id == int(OWNER_ID):
        await message.answer("لوحة تحكم المدير: هنا تضع أوامر الإدارة", reply_markup=get_owner_keyboard())
    else:
        await message.answer("غير مصرح لك باستخدام هذه الأوامر.")

@dp.message(Text("عدد المستخدمين"))
async def cmd_users(message: types.Message):
    if message.from_user.id == int(OWNER_ID):
        with SessionLocal() as session:
            count = session.query(User).count()
        await message.reply(f"عدد المستخدمين: {count}")
    else:
        await message.reply("غير مصرح لك.")

@dp.message(Text("عدد المستخدمين أونلاين"))
async def cmd_online_users(message: types.Message):
    if message.from_user.id == int(OWNER_ID):
        # هذا مجرد مثال، تحتاج لتنفيذ عداد حقيقي للأونلاين
        await message.reply("عدد المستخدمين أونلاين: 5 (مثال فقط)")
    else:
        await message.reply("غير مصرح لك.")

@dp.message(Text("تقارير الاستثمار"))
async def cmd_reports(message: types.Message):
    if message.from_user.id == int(OWNER_ID):
        await message.reply("تقارير الاستثمار: (ميزة تحت التطوير)")
    else:
        await message.reply("غير مصرح لك.")

@dp.message(Text("حالة البوت البرمجية"))
async def cmd_bot_status(message: types.Message):
    if message.from_user.id == int(OWNER_ID):
        await message.reply("البوت يعمل بشكل طبيعي. لا توجد مشاكل حالياً.")
    else:
        await message.reply("غير مصرح لك.")

async def main():
    print("البوت بدأ العمل")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())