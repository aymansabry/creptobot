import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, Text
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from sqlalchemy import and_
from cryptography.fernet import Fernet, InvalidToken
import datetime
import ccxt

from database import create_tables, SessionLocal
from models import User, APIKey, TradeLog
from settings import BOT_TOKEN, OWNER_ID, FERNET_KEY

# إنشاء الجداول قبل بدء البوت
create_tables()

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

fernet = Fernet(FERNET_KEY.encode())

# إدارة الحالات للحوار
class InvestmentStates(StatesGroup):
    waiting_for_exchange_name = State()
    waiting_for_api_key = State()
    waiting_for_api_secret = State()
    waiting_for_investment_amount = State()
    waiting_for_start_date = State()

# قوائم المستخدمين
user_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="تسجيل/تعديل بيانات التداول")],
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
        [KeyboardButton(text="حالة البوت البرمجية")]
    ],
    resize_keyboard=True
)

def safe_decrypt(token):
    try:
        return fernet.decrypt(token.encode()).decode()
    except InvalidToken:
        return None

async def verify_api_key(exchange_name, api_key, api_secret):
    """تحقق من صلاحية مفاتيح API عبر ccxt"""
    try:
        exchange_class = getattr(ccxt, exchange_name)
    except AttributeError:
        return False, "اسم المنصة غير مدعوم."

    try:
        exchange = exchange_class({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
        })
        # اختبار بسيط: طلب رصيد الحساب
        balance = await asyncio.to_thread(exchange.fetch_balance)
        if balance:
            return True, "المفاتيح صحيحة."
        else:
            return False, "تعذر الحصول على بيانات الرصيد."
    except Exception as e:
        return False, f"خطأ أثناء التحقق: {str(e)}"

async def run_investment_for_user(user: User):
    """تشغيل الاستثمار الحقيقي للمستخدم"""
    with SessionLocal() as session:
        api_keys = session.query(APIKey).filter(
            APIKey.user_id == user.id,
            APIKey.is_active == True
        ).all()

    for key in api_keys:
        exchange_name = key.exchange
        api_key = safe_decrypt(key.api_key_encrypted)
        api_secret = safe_decrypt(key.api_secret_encrypted)
        if not api_key or not api_secret:
            continue

        try:
            exchange_class = getattr(ccxt, exchange_name)
            exchange = exchange_class({
                'apiKey': api_key,
                'secret': api_secret,
                'enableRateLimit': True,
            })

            # مثال استثمار: شراء كمية بسيطة من BTC/USDT
            symbol = 'BTC/USDT'
            amount = 0.001  # مثال كمية

            # جلب السعر الحالي
            ticker = await asyncio.to_thread(exchange.fetch_ticker, symbol)
            price = ticker['last']

            # تنفيذ أمر شراء
            order = await asyncio.to_thread(exchange.create_market_buy_order, symbol, amount)

            # حفظ السجل في قاعدة البيانات
            with SessionLocal() as session:
                trade_log = TradeLog(
                    user_id=user.id,
                    exchange=exchange_name,
                    side='buy',
                    symbol=symbol,
                    qty=amount,
                    price=price,
                    profit=None,
                    raw=str(order),
                    status='OK',
                    error=None
                )
                session.add(trade_log)
                session.commit()

        except Exception as e:
            with SessionLocal() as session:
                trade_log = TradeLog(
                    user_id=user.id,
                    exchange=exchange_name,
                    side='buy',
                    symbol='BTC/USDT',
                    qty=0,
                    price=0,
                    profit=None,
                    raw='',
                    status='FAILED',
                    error=str(e)
                )
                session.add(trade_log)
                session.commit()

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
async def handle_api_key_entry(message: types.Message, state: FSMContext):
    await message.answer(
        "أدخل اسم المنصة (مثلاً: binance):",
        reply_markup=ReplyKeyboardRemove()
    )
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
    await message.answer("أدخل السر السري (API Secret) للمنصة:")
    await state.set_state(InvestmentStates.waiting_for_api_secret)

@dp.message(state=InvestmentStates.waiting_for_api_secret)
async def process_api_secret(message: types.Message, state: FSMContext):
    api_secret = message.text.strip()
    data = await state.get_data()
    exchange_name = data.get('exchange_name')
    api_key = data.get('api_key')

    # تحقق من صحة المفاتيح
    valid, msg = await verify_api_key(exchange_name, api_key, api_secret)
    if not valid:
        await message.answer(f"خطأ في التحقق من المفاتيح: {msg}\nأعد المحاولة من فضلك.")
        return

    # تخزين المفتاح في قاعدة البيانات (مشفر)
    encrypted_key = fernet.encrypt(api_key.encode()).decode()
    encrypted_secret = fernet.encrypt(api_secret.encode()).decode()

    with SessionLocal() as session:
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if not user:
            user = User(telegram_id=message.from_user.id, is_active=True)
            session.add(user)
            session.commit()

        api_key_obj = session.query(APIKey).filter_by(user_id=user.id, exchange=exchange_name).first()
        if api_key_obj:
            api_key_obj.api_key_encrypted = encrypted_key
            api_key_obj.api_secret_encrypted = encrypted_secret
            api_key_obj.is_active = True
        else:
            api_key_obj = APIKey(
                user_id=user.id,
                exchange=exchange_name,
                api_key_encrypted=encrypted_key,
                api_secret_encrypted=encrypted_secret,
                is_active=True
            )
            session.add(api_key_obj)
        session.commit()

    await message.answer(f"تم حفظ بيانات منصة {exchange_name} بنجاح.", reply_markup=user_keyboard)
    await state.clear()

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

        # تعيين المبلغ
        user.investment_amount = amount
        user.is_active = True
        session.commit()

    await message.answer(f"تم تعيين مبلغ الاستثمار: {amount} بنجاح.\nيتم الآن بدء الاستثمار الآلي...", reply_markup=user_keyboard)
    await state.clear()

    # بدء الاستثمار الحقيقي
    await run_investment_for_user(user)

@dp.message(Text("استثمار وهمي"))
async def demo_investment(message: types.Message):
    await message.answer("تم بدء الاستثمار الوهمي. (سيتم تنفيذ المحاكاة لاحقاً)", reply_markup=user_keyboard)

@dp.message(Text("كشف حساب عن فترة"))
async def request_start_date(message: types.Message, state: FSMContext):
    await message.answer("أدخل تاريخ بداية الفترة (مثلاً: 2023-01-01):", reply_markup=ReplyKeyboardRemove())
    await state.set_state(InvestmentStates.waiting_for_start_date)

@dp.message(state=InvestmentStates.waiting_for_start_date)
async def process_start_date(message: types.Message, state: FSMContext):
    try:
        start_date = datetime.datetime.strptime(message.text.strip(), "%Y-%m-%d")
    except ValueError:
        await message.answer("صيغة التاريخ غير صحيحة. يرجى إدخال التاريخ بصيغة YYYY-MM-DD.")
        return

    with SessionLocal() as session:
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if not user:
            await message.answer("لم يتم العثور على بيانات المستخدم.")
            await state.clear()
            return

        # جلب السجلات خلال الفترة
        logs = session.query(TradeLog).filter(
            TradeLog.user_id == user.id,
            TradeLog.created_at >= start_date
        ).all()

        if not logs:
            await message.answer("لا توجد بيانات خلال هذه الفترة.", reply_markup=user_keyboard)
            await state.clear()
            return

        report_lines = []
        for log in logs:
            date_str = log.created_at.strftime("%Y-%m-%d %H:%M")
            line = f"{date_str} | {log.exchange} | {log.side} {log.qty} {log.symbol} @ {log.price}"
            report_lines.append(line)

        report = "\n".join(report_lines)
        if len(report) > 4000:
            report = report[:4000] + "\n..."

        await message.answer(f"تقرير الاستثمار:\n{report}", reply_markup=user_keyboard)
        await state.clear()

@dp.message(Text("حالة السوق"))
async def market_status(message: types.Message):
    # مثال تحليل مبسط للسوق
    await message.answer(
        "تحليل حالة السوق الحالية:\n"
        "- السوق يميل للصعود اليوم.\n"
        "- أنصح بالتركيز على BTC و ETH.\n"
        "- راقب الأخبار العالمية.\n",
        reply_markup=user_keyboard
    )

@dp.message(Text("ايقاف الاستثمار"))
async def stop_investment(message: types.Message):
    with SessionLocal() as session:
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if user:
            user.is_active = False
            session.commit()
            await message.answer("تم إيقاف استثمارك بنجاح.", reply_markup=user_keyboard)
        else:
            await message.answer("لم يتم العثور على بياناتك.", reply_markup=user_keyboard)

# أوامر المدير
@dp.message(Text("تعديل نسبة ربح البوت"))
async def edit_profit_percentage(message: types.Message):
    if message.from_user.id != int(OWNER_ID):
        await message.answer("غير مصرح لك.")
        return
    await message.answer("هنا يتم تعديل نسبة ربح البوت. (لم يتم تنفيذها بعد)")

@dp.message(Text("عدد المستخدمين"))
async def count_users(message: types.Message):
    if message.from_user.id != int(OWNER_ID):
        await message.answer("غير مصرح لك.")
        return
    with SessionLocal() as session:
        count = session.query(User).count()
    await message.answer(f"عدد المستخدمين: {count}")

@dp.message(Text("عدد المستخدمين أونلاين"))
async def count_online_users(message: types.Message):
    if message.from_user.id != int(OWNER_ID):
        await message.answer("غير مصرح لك.")
        return
    # يمكن إضافة لوجيك التتبع حسب الحاجة
    await message.answer("عدد المستخدمين أونلاين: (لم يتم تنفيذه)")

@dp.message(Text("تقارير الاستثمار"))
async def investment_reports(message: types.Message):
    if message.from_user.id != int(OWNER_ID):
        await message.answer("غير مصرح لك.")
        return
    # يمكن تطوير تقارير متقدمة حسب الحاجة
    await message.answer("تقرير الاستثمار (لم يتم تنفيذه بعد)")

@dp.message(Text("حالة البوت البرمجية"))
async def bot_status(message: types.Message):
    if message.from_user.id != int(OWNER_ID):
        await message.answer("غير مصرح لك.")
        return
    await message.answer("البوت يعمل بشكل طبيعي (لم يتم تنفيذ تفاصيل الفحص بعد)")

async def main():
    print("البوت بدأ العمل")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())