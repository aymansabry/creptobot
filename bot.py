import asyncio
import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, Text
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from sqlalchemy.orm import Session
from cryptography.fernet import Fernet, InvalidToken
import ccxt

from database import create_tables, SessionLocal
from models import User, APIKey, TradeLog
from settings import BOT_TOKEN, OWNER_ID, FERNET_KEY

create_tables()

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

fernet = Fernet(FERNET_KEY.encode())

# ---- FSM States ----
class InvestmentStates(StatesGroup):
    waiting_for_exchange_name = State()
    waiting_for_api_key = State()
    waiting_for_api_secret = State()
    waiting_for_passphrase = State()
    waiting_for_investment_amount = State()
    waiting_for_start_date = State()
    waiting_for_end_date = State()
    # يمكن إضافة حالات أخرى حسب الحاجة


# ---- لوحة المفاتيح ----

user_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton("/help"), KeyboardButton("تسجيل/تعديل بيانات التداول")],
        [KeyboardButton("ابدأ استثمار"), KeyboardButton("استثمار وهمي")],
        [KeyboardButton("كشف حساب عن فترة"), KeyboardButton("حالة السوق")],
        [KeyboardButton("ايقاف الاستثمار")]
    ], resize_keyboard=True
)

owner_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton("/help"), KeyboardButton("/admin_panel")],
        [KeyboardButton("تعديل نسبة ربح البوت"), KeyboardButton("عدد المستخدمين")],
        [KeyboardButton("عدد المستخدمين أونلاين"), KeyboardButton("تقارير الاستثمار")],
        [KeyboardButton("حالة البوت البرمجية")],
        [KeyboardButton("تفعيل وضع المدير"), KeyboardButton("تفعيل وضع المستخدم")]
    ], resize_keyboard=True
)

# ---- دوال مساعدة ----

def safe_decrypt(token: str) -> str | None:
    try:
        return fernet.decrypt(token.encode()).decode()
    except InvalidToken:
        return None

def safe_encrypt(data: str) -> str:
    return fernet.encrypt(data.encode()).decode()

def generate_date_selection_keyboard(base_date: datetime.date, days_range=10) -> InlineKeyboardMarkup:
    """
    ينشئ لوحة اختيار تاريخ تبدأ من base_date وتمتد لـ days_range يوم.
    يظهر التاريخ في أزرار بشكل YYYY-MM-DD.
    """
    keyboard = InlineKeyboardMarkup(row_width=3)
    buttons = []
    for i in range(days_range):
        day = base_date + datetime.timedelta(days=i)
        btn = InlineKeyboardButton(text=day.strftime("%Y-%m-%d"), callback_data=f"select_date:{day.isoformat()}")
        buttons.append(btn)
    keyboard.add(*buttons)
    return keyboard

# --- أوامر البداية ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if message.from_user.id == int(OWNER_ID):
        await message.answer("أهلاً مالك البوت!", reply_markup=owner_keyboard)
    else:
        await message.answer("أهلاً! البوت يعمل بنجاح.", reply_markup=user_keyboard)

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "هذه أوامر البوت المتاحة:\n"
        "/start\n/help\n"
        "تسجيل/تعديل بيانات التداول\n"
        "ابدأ استثمار\n"
        "استثمار وهمي\n"
        "كشف حساب عن فترة\n"
        "حالة السوق\n"
        "ايقاف الاستثمار"
    )


# --- تبديل أوضاع المدير والمستخدم ---
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

# --- تسجيل / تعديل بيانات التداول ---
@dp.message(Text("تسجيل/تعديل بيانات التداول"))
async def start_register_api(message: types.Message, state: FSMContext):
    await message.answer("يرجى إدخال اسم المنصة (مثل binance, kucoin):", reply_markup=ReplyKeyboardRemove())
    await state.set_state(InvestmentStates.waiting_for_exchange_name)

@dp.message(state=InvestmentStates.waiting_for_exchange_name)
async def process_exchange_name(message: types.Message, state: FSMContext):
    exchange_name = message.text.strip().lower()
    await state.update_data(exchange_name=exchange_name)
    await message.answer("أدخل مفتاح API الخاص بالمنصة:")
    await state.set_state(InvestmentStates.waiting_for_api_key)

@dp.message(state=InvestmentStates.waiting_for_api_key)
async def process_api_key(message: types.Message, state: FSMContext):
    api_key = message.text.strip()
    await state.update_data(api_key=api_key)
    await message.answer("أدخل الـ API Secret الخاص بالمنصة:")
    await state.set_state(InvestmentStates.waiting_for_api_secret)

@dp.message(state=InvestmentStates.waiting_for_api_secret)
async def process_api_secret(message: types.Message, state: FSMContext):
    api_secret = message.text.strip()
    await state.update_data(api_secret=api_secret)
    await message.answer("إذا كانت المنصة تستخدم Passphrase، أدخله الآن، أو اكتب 'لا' للتخطي:")
    await state.set_state(InvestmentStates.waiting_for_passphrase)

@dp.message(state=InvestmentStates.waiting_for_passphrase)
async def process_passphrase(message: types.Message, state: FSMContext):
    passphrase = message.text.strip()
    if passphrase.lower() == 'لا':
        passphrase = None

    data = await state.get_data()
    exchange_name = data['exchange_name']
    api_key = data['api_key']
    api_secret = data['api_secret']

    # تحقق مفاتيح API
    try:
        exchange_class = getattr(ccxt, exchange_name)
    except AttributeError:
        await message.answer("اسم منصة غير مدعوم. يرجى البدء مجددًا.")
        await state.clear()
        return

    exchange_params = {'apiKey': api_key, 'secret': api_secret}
    if passphrase:
        exchange_params['password'] = passphrase

    exchange = exchange_class(exchange_params)

    try:
        await asyncio.to_thread(exchange.fetch_balance)
    except Exception as e:
        await message.answer(f"خطأ في التحقق من مفاتيح API: {str(e)}\nيرجى المحاولة مرة أخرى.")
        await state.clear()
        return

    with SessionLocal() as session:
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if not user:
            user = User(telegram_id=message.from_user.id, role='client')
            session.add(user)
            session.commit()
            session.refresh(user)

        # تعطيل مفاتيح قديمة لنفس المنصة
        session.query(APIKey).filter(
            APIKey.user_id == user.id,
            APIKey.exchange == exchange_name,
            APIKey.is_active == True
        ).update({"is_active": False})

        new_key = APIKey(
            user_id=user.id,
            exchange=exchange_name,
            api_key_encrypted=safe_encrypt(api_key),
            api_secret_encrypted=safe_encrypt(api_secret),
            passphrase_encrypted=safe_encrypt(passphrase) if passphrase else None,
            is_active=True,
            created_at=datetime.datetime.utcnow()
        )
        session.add(new_key)
        session.commit()

    await message.answer(f"تم تسجيل مفاتيح منصة {exchange_name} بنجاح.")
    await state.clear()


# --- بدء استثمار حقيقي ---
@dp.message(Text("ابدأ استثمار"))
async def start_investment(message: types.Message, state: FSMContext):
    with SessionLocal() as session:
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if not user or not user.api_keys:
            await message.answer("يجب تسجيل بيانات التداول أولاً عبر 'تسجيل/تعديل بيانات التداول'.")
            return
        if hasattr(user, 'is_active') and not user.is_active:
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
        user.investment_amount = amount
        user.is_active = True
        session.commit()

    await message.answer(f"تم تعيين مبلغ الاستثمار: {amount} بنجاح.\nيتم الآن بدء الاستثمار الآلي...")
    await state.clear()

    await run_investment_for_user(user)

async def run_investment_for_user(user: User):
    # تنفيذ استثمار حقيقي - نموذج أولي
    with SessionLocal() as session:
        api_keys = session.query(APIKey).filter(
            APIKey.user_id == user.id,
            APIKey.is_active == True
        ).all()

    for key in api_keys:
        exchange_name = key.exchange
        api_key = safe_decrypt(key.api_key_encrypted)
        api_secret = safe_decrypt(key.api_secret_encrypted)
        passphrase = safe_decrypt(key.passphrase_encrypted) if key.passphrase_encrypted else None

        exchange_class = getattr(ccxt, exchange_name)
        exchange_params = {'apiKey': api_key, 'secret': api_secret}
        if passphrase:
            exchange_params['password'] = passphrase

        exchange = exchange_class(exchange_params)
        # مثال: شراء عملة BTC بمبلغ الاستثمار (اختياري: استبدل بالمنطق الفعلي)
        try:
            balance = await asyncio.to_thread(exchange.fetch_balance)
            # تنفيذ أوامر الشراء هنا حسب المنطق
            print(f"تشغيل استثمار على منصة {exchange_name} للمستخدم {user.telegram_id}")
        except Exception as e:
            print(f"خطأ أثناء تنفيذ الاستثمار: {e}")

# --- استثمار وهمي ---
@dp.message(Text("استثمار وهمي"))
async def fake_investment(message: types.Message):
    await message.answer("بدأ الاستثمار الوهمي، هذا مجرد محاكاة بدون استخدام أموال حقيقية.")

# --- كشف حساب عن فترة (باستخدام اختيار تواريخ من أزرار) ---
@dp.message(Text("كشف حساب عن فترة"))
async def start_report_period(message: types.Message, state: FSMContext):
    today = datetime.date.today()
    keyboard = generate_date_selection_keyboard(today, days_range=15)
    await message.answer("اختر تاريخ بداية الفترة:", reply_markup=keyboard)
    await state.set_state(InvestmentStates.waiting_for_start_date)

@dp.callback_query(lambda c: c.data and c.data.startswith("select_date:"))
async def process_date_selection(callback: types.CallbackQuery, state: FSMContext):
    selected_date_str = callback.data.split(":")[1]
    selected_date = datetime.date.fromisoformat(selected_date_str)
    current_state = await state.get_state()

    if current_state == InvestmentStates.waiting_for_start_date.state:
        await state.update_data(start_date=selected_date)
        # اطلب اختيار تاريخ النهاية (نفس طريقة البداية مع بدء من start_date)
        keyboard = generate_date_selection_keyboard(selected_date, days_range=15)
        await callback.message.edit_text(f"تاريخ البداية محدد: {selected_date}\nالآن اختر تاريخ النهاية:", reply_markup=keyboard)
        await state.set_state(InvestmentStates.waiting_for_end_date)
        await callback.answer()

    elif current_state == InvestmentStates.waiting_for_end_date.state:
        data = await state.get_data()
        start_date = data.get("start_date")

        if selected_date < start_date:
            await callback.answer("يجب اختيار تاريخ نهاية بعد تاريخ البداية.", show_alert=True)
            return

        await state.update_data(end_date=selected_date)
        # الآن جهز التقرير بناء على start_date و end_date
        with SessionLocal() as session:
            user = session.query(User).filter_by(telegram_id=callback.from_user.id).first()
            if not user:
                await callback.message.answer("لم يتم العثور على بيانات المستخدم.")
                await state.clear()
                await callback.answer()
                return

            # جلب سجلات التداول للفترة
            # trade_logs = session.query(TradeLog).filter(
            #     TradeLog.user_id == user.id,
            #     TradeLog.created_at >= start_date,
            #     TradeLog.created_at <= selected_date
            # ).all()
            # إعداد تقرير نموذجي:
            report_msg = (
                f"تقرير كشف حساب من {start_date} إلى {selected_date}:\n"
                "(التقارير التفصيلية قيد التطوير...)"
            )

        await callback.message.edit_text(report_msg, reply_markup=ReplyKeyboardRemove())
        await state.clear()
        await callback.answer()

# --- حالة السوق ---
@dp.message(Text("حالة السوق"))
async def market_status(message: types.Message):
    # يمكن ربط API خارجي لتحليل السوق أو استخدام بيانات تجريبية
    await message.answer("تحليل السوق الحالي:\nالسوق صاعد/هابط... (رسالة تجريبية)")

# --- إيقاف الاستثمار ---
@dp.message(Text("ايقاف الاستثمار"))
async def stop_investment(message: types.Message):
    with SessionLocal() as session:
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if not user:
            await message.answer("لم يتم العثور على بيانات المستخدم.")
            return
        user.is_active = False
        session.commit()
    await message.answer("تم إيقاف الاستثمار الخاص بك.")

# --- أوامر المدير ---
@dp.message(Command("admin_panel"))
async def admin_panel(message: types.Message):
    if message.from_user.id != int(OWNER_ID):
        await message.answer("غير مصرح لك.")
        return
    await message.answer("لوحة تحكم المدير: (قيد التطوير)")

@dp.message(Text("عدد المستخدمين"))
async def user_count(message: types.Message):
    if message.from_user.id != int(OWNER_ID):
        await message.answer("غير مصرح لك.")
        return
    with SessionLocal() as session:
        count = session.query(User).count()
    await message.answer(f"عدد المستخدمين الكلي: {count}")

@dp.message(Text("عدد المستخدمين أونلاين"))
async def user_online_count(message: types.Message):
    if message.from_user.id != int(OWNER_ID):
        await message.answer("غير مصرح لك.")
        return
    # يمكن إضافة نظام تتبع أونلاين لاحقاً
    await message.answer("عدد المستخدمين أونلاين: (ميزة قيد التطوير)")

@dp.message(Text("تقارير الاستثمار"))
async def investment_reports(message: types.Message):
    if message.from_user.id != int(OWNER_ID):
        await message.answer("غير مصرح لك.")
        return
    await message.answer("تقارير الاستثمار: (قيد التطوير)")

@dp.message(Text("حالة البوت البرمجية"))
async def bot_status(message: types.Message):
    if message.from_user.id != int(OWNER_ID):
        await message.answer("غير مصرح لك.")
        return
    await message.answer("البوت يعمل بشكل طبيعي.")

# --- بدء التشغيل ---
async def main():
    print("البوت بدأ العمل")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())