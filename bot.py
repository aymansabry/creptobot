import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, Text
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from sqlalchemy import and_
from cryptography.fernet import Fernet, InvalidToken
import ccxt
import datetime

from database import create_tables, SessionLocal
from models import User, APIKey, TradeLog
from settings import BOT_TOKEN, OWNER_ID, FERNET_KEY

# إنشاء الجداول قبل بدء البوت
create_tables()

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

fernet = Fernet(FERNET_KEY.encode())

# تعريف حالات FSM للاستثمار
class InvestmentStates(StatesGroup):
    waiting_for_exchange_name = State()
    waiting_for_api_key = State()
    waiting_for_api_secret = State()
    waiting_for_passphrase = State()
    waiting_for_investment_amount = State()
    # أضف حالات أخرى حسب الحاجة

# قوائم المستخدمين
user_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/help"), KeyboardButton(text="تسجيل/تعديل بيانات التداول")],
        [KeyboardButton(text="ابدأ استثمار"), KeyboardButton(text="استثمار وهمي")],
        [KeyboardButton(text="كشف حساب عن فترة"), KeyboardButton(text="حالة السوق")],
        [KeyboardButton(text="ايقاف الاستثمار")]
    ],
    resize_keyboard=True
)

owner_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/help"), KeyboardButton(text="/admin_panel")],
        [KeyboardButton(text="تعديل نسبة ربح البوت"), KeyboardButton(text="عدد المستخدمين")],
        [KeyboardButton(text="عدد المستخدمين أونلاين"), KeyboardButton(text="تقارير الاستثمار")],
        [KeyboardButton(text="حالة البوت البرمجية"), KeyboardButton(text="تفعيل وضع المدير")],
        [KeyboardButton(text="تفعيل وضع المستخدم")]
    ],
    resize_keyboard=True
)

def safe_decrypt(token):
    try:
        return fernet.decrypt(token.encode()).decode()
    except InvalidToken:
        return None

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if message.from_user.id == int(OWNER_ID):
        await message.answer("أهلاً مالك البوت!", reply_markup=owner_keyboard)
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

@dp.message(Text("تسجيل/تعديل بيانات التداول"))
async def start_api_key_registration(message: types.Message, state: FSMContext):
    await message.answer("يرجى إدخال اسم المنصة (exchange name):", reply_markup=ReplyKeyboardRemove())
    await state.set_state(InvestmentStates.waiting_for_exchange_name)

@dp.message(F.state == InvestmentStates.waiting_for_exchange_name)
async def process_exchange_name(message: types.Message, state: FSMContext):
    exchange_name = message.text.strip()
    await state.update_data(exchange_name=exchange_name)
    await message.answer("الآن أدخل مفتاح API الخاص بالمنصة:")
    await state.set_state(InvestmentStates.waiting_for_api_key)

@dp.message(F.state == InvestmentStates.waiting_for_api_key)
async def process_api_key(message: types.Message, state: FSMContext):
    api_key = message.text.strip()
    await state.update_data(api_key=api_key)
    await message.answer("الآن أدخل السر الخاص بـ API:")
    await state.set_state(InvestmentStates.waiting_for_api_secret)

@dp.message(F.state == InvestmentStates.waiting_for_api_secret)
async def process_api_secret(message: types.Message, state: FSMContext):
    api_secret = message.text.strip()
    await state.update_data(api_secret=api_secret)
    await message.answer("إن كان هناك passphrase، أدخله الآن (أو ارسل 'لا' لتخطي):")
    await state.set_state(InvestmentStates.waiting_for_passphrase)

@dp.message(F.state == InvestmentStates.waiting_for_passphrase)
async def process_passphrase(message: types.Message, state: FSMContext):
    passphrase = message.text.strip()
    if passphrase.lower() == "لا":
        passphrase = None
    data = await state.get_data()

    exchange_name = data.get("exchange_name")
    api_key = data.get("api_key")
    api_secret = data.get("api_secret")

    # تحقق من صحة المفاتيح باستخدام ccxt
    try:
        exchange_class = getattr(ccxt, exchange_name.lower())
        exchange = exchange_class({
            'apiKey': api_key,
            'secret': api_secret,
        })
        if passphrase:
            exchange.password = passphrase

        await asyncio.get_event_loop().run_in_executor(None, exchange.load_markets)
    except Exception as e:
        await message.answer(f"فشل التحقق من المفاتيح: {str(e)}\nأعد المحاولة.")
        return

    # التشفير والتخزين في قاعدة البيانات
    encrypted_api_key = fernet.encrypt(api_key.encode()).decode()
    encrypted_api_secret = fernet.encrypt(api_secret.encode()).decode()
    encrypted_passphrase = fernet.encrypt(passphrase.encode()).decode() if passphrase else None

    with SessionLocal() as session:
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if not user:
            user = User(telegram_id=message.from_user.id)
            session.add(user)
            session.commit()
        # تحقق إذا المنصة موجودة مسبقاً، حدثها أو أضف واحدة جديدة
        existing_key = session.query(APIKey).filter(
            APIKey.user_id == user.id,
            APIKey.exchange == exchange_name
        ).first()
        if existing_key:
            existing_key.api_key_encrypted = encrypted_api_key
            existing_key.api_secret_encrypted = encrypted_api_secret
            existing_key.passphrase_encrypted = encrypted_passphrase
            existing_key.is_active = True
        else:
            new_key = APIKey(
                user_id=user.id,
                exchange=exchange_name,
                api_key_encrypted=encrypted_api_key,
                api_secret_encrypted=encrypted_api_secret,
                passphrase_encrypted=encrypted_passphrase,
                is_active=True
            )
            session.add(new_key)
        session.commit()

    await message.answer(f"تم حفظ بيانات منصة {exchange_name} بنجاح.")
    await state.clear()
    await message.answer("يمكنك إضافة منصة أخرى أو العودة إلى القائمة الرئيسية.", reply_markup=user_keyboard)

@dp.message(Text("ابدأ استثمار"))
async def start_investment(message: types.Message, state: FSMContext):
    with SessionLocal() as session:
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if not user or not user.api_keys:
            await message.answer("يجب تسجيل بيانات التداول أولاً عبر 'تسجيل/تعديل بيانات التداول'.")
            return
        if not user.is_active:
            await message.answer("تم إيقاف الاستثمار الخاص بك، لا يمكنك البدء حالياً.")
            return

    await message.answer("أدخل مبلغ الاستثمار (مثلاً: 1000):", reply_markup=ReplyKeyboardRemove())
    await state.set_state(InvestmentStates.waiting_for_investment_amount)

@dp.message(F.state == InvestmentStates.waiting_for_investment_amount)
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

        user.investment_amount = amount
        user.is_active = True
        session.commit()

    await message.answer(f"تم تعيين مبلغ الاستثمار: {amount} بنجاح.\nيتم الآن بدء الاستثمار الآلي...")
    await state.clear()

    # هنا يمكن استدعاء دالة بدء عملية الاستثمار الحقيقية (async)
    # await run_real_investment(user)

@dp.message(Text("استثمار وهمي"))
async def fake_investment(message: types.Message):
    await message.answer("تم بدء الاستثمار الوهمي (محاكاة).")

@dp.message(Text("كشف حساب عن فترة"))
async def account_statement(message: types.Message, state: FSMContext):
    await message.answer("يرجى إدخال تاريخ البداية (YYYY-MM-DD):", reply_markup=ReplyKeyboardRemove())
    await state.set_state("waiting_for_start_date")

@dp.message(F.state == "waiting_for_start_date")
async def process_start_date(message: types.Message, state: FSMContext):
    date_text = message.text.strip()
    try:
        start_date = datetime.datetime.strptime(date_text, "%Y-%m-%d")
    except ValueError:
        await message.answer("صيغة التاريخ غير صحيحة، يرجى المحاولة مرة أخرى.")
        return
    await state.update_data(start_date=start_date)
    await message.answer("يرجى إدخال تاريخ النهاية (YYYY-MM-DD):")
    await state.set_state("waiting_for_end_date")

@dp.message(F.state == "waiting_for_end_date")
async def process_end_date(message: types.Message, state: FSMContext):
    date_text = message.text.strip()
    try:
        end_date = datetime.datetime.strptime(date_text, "%Y-%m-%d")
    except ValueError:
        await message.answer("صيغة التاريخ غير صحيحة، يرجى المحاولة مرة أخرى.")
        return
    data = await state.get_data()
    start_date = data.get("start_date")

    if end_date < start_date:
        await message.answer("تاريخ النهاية لا يمكن أن يكون قبل تاريخ البداية.")
        return

    with SessionLocal() as session:
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if not user:
            await message.answer("لم يتم العثور على بيانات المستخدم.")
            await state.clear()
            return
        logs = session.query(TradeLog).filter(
            TradeLog.user_id == user.id,
            TradeLog.created_at >= start_date,
            TradeLog.created_at <= end_date
        ).all()

    if not logs:
        await message.answer("لا توجد سجلات تداول في هذه الفترة.")
    else:
        report_lines = [f"تقرير التداول من {start_date.date()} إلى {end_date.date()}:"]
        for log in logs:
            report_lines.append(f"{log.created_at.date()} - {log.exchange} - {log.side} {log.symbol} @ {log.price} - الربح: {log.profit or 0}")
        await message.answer("\n".join(report_lines))

    await state.clear()
    await message.answer("تم الانتهاء من كشف الحساب.", reply_markup=user_keyboard)

@dp.message(Text("حالة السوق"))
async def market_status(message: types.Message):
    # يمكن هنا إضافة التحليل والنصائح الحقيقية
    await message.answer("تحليل حالة السوق حالياً:\nالسوق مستقر مع بعض التقلبات...")

@dp.message(Text("ايقاف الاستثمار"))
async def stop_investment(message: types.Message):
    with SessionLocal() as session:
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if not user:
            await message.answer("لم يتم العثور على بيانات المستخدم.")
            return
        user.is_active = False
        session.commit()
    await message.answer("تم إيقاف الاستثمار الخاص بك بنجاح.")

# أوامر المدير

@dp.message(Text("تعديل نسبة ربح البوت"))
async def change_profit_rate(message: types.Message):
    if message.from_user.id != int(OWNER_ID):
        await message.answer("غير مصرح لك باستخدام هذه الأوامر.")
        return
    await message.answer("أدخل نسبة الربح الجديدة (مثلاً 5%):")

@dp.message(Text("عدد المستخدمين"))
async def get_users_count(message: types.Message):
    if message.from_user.id != int(OWNER_ID):
        await message.answer("غير مصرح لك.")
        return
    with SessionLocal() as session:
        count = session.query(User).count()
    await message.answer(f"عدد المستخدمين الكلي: {count}")

@dp.message(Text("عدد المستخدمين أونلاين"))
async def get_online_users_count(message: types.Message):
    if message.from_user.id != int(OWNER_ID):
        await message.answer("غير مصرح لك.")
        return
    # تحتاج لآلية تتبع أونلاين (يمكن تطويرها لاحقاً)
    await message.answer("عدد المستخدمين أونلاين: غير متوفر حالياً.")

@dp.message(Text("تقارير الاستثمار"))
async def investment_reports(message: types.Message):
    if message.from_user.id != int(OWNER_ID):
        await message.answer("غير مصرح لك.")
        return
    await message.answer("تقارير الاستثمار: قيد التطوير...")

@dp.message(Text("حالة البوت البرمجية"))
async def bot_status(message: types.Message):
    if message.from_user.id != int(OWNER_ID):
        await message.answer("غير مصرح لك.")
        return
    await message.answer("البوت يعمل بشكل طبيعي.")

@dp.message(Text("تفعيل وضع المدير"))
async def activate_admin_mode(message: types.Message):
    if message.from_user.id != int(OWNER_ID):
        await message.answer("غير مصرح لك.")
        return
    await message.answer("تم تفعيل وضع المدير.", reply_markup=owner_keyboard)

@dp.message(Text("تفعيل وضع المستخدم"))
async def activate_user_mode(message: types.Message):
    if message.from_user.id != int(OWNER_ID):
        await message.answer("غير مصرح لك.")
        return
    await message.answer("تم تفعيل وضع المستخدم.", reply_markup=user_keyboard)


async def main():
    print("البوت بدأ العمل")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())