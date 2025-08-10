import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, Text
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import and_
from cryptography.fernet import Fernet, InvalidToken
import datetime
import ccxt.async_support as ccxt_async

from database import create_tables, SessionLocal
from models import User, APIKey, TradeLog
from settings import BOT_TOKEN, OWNER_ID, FERNET_KEY

create_tables()

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

fernet = Fernet(FERNET_KEY.encode())

# ----- حالات FSM -----
class InvestmentStates(StatesGroup):
    waiting_for_exchange_name = State()
    waiting_for_api_key = State()
    waiting_for_api_secret = State()
    waiting_for_passphrase = State()
    waiting_for_investment_amount = State()
    waiting_for_report_start_date = State()
    waiting_for_report_end_date = State()

# ----- لوحات المفاتيح -----
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
        [KeyboardButton(text="حالة البوت البرمجية")]
    ],
    resize_keyboard=True
)

# ----- تشفير وفك تشفير -----
def safe_encrypt(text):
    return fernet.encrypt(text.encode()).decode()

def safe_decrypt(token):
    try:
        return fernet.decrypt(token.encode()).decode()
    except InvalidToken:
        return None

# ----- بداية أوامر البوت -----

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if message.from_user.id == int(OWNER_ID):
        await message.answer("أهلاً مالك البوت!", reply_markup=owner_keyboard)
    else:
        with SessionLocal() as session:
            user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
            if not user:
                user = User(telegram_id=message.from_user.id)
                session.add(user)
                session.commit()
        await message.answer("أهلاً! البوت يعمل بنجاح.", reply_markup=user_keyboard)

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.reply(
        "أوامر البوت:\n"
        "/start\n"
        "/help\n"
        "تسجيل/تعديل بيانات التداول\n"
        "ابدأ استثمار\n"
        "استثمار وهمي\n"
        "كشف حساب عن فترة\n"
        "حالة السوق\n"
        "ايقاف الاستثمار\n"
    )

# ----- تسجيل / تعديل بيانات التداول -----

@dp.message(Text("تسجيل/تعديل بيانات التداول"))
async def start_api_key_registration(message: types.Message, state: FSMContext):
    exchanges = ['binance', 'kucoin', 'coinbasepro', 'bitfinex']
    keyboard = InlineKeyboardMarkup(row_width=2)
    for ex in exchanges:
        keyboard.insert(InlineKeyboardButton(text=ex.capitalize(), callback_data=f"select_exchange_{ex}"))
    await message.answer("اختر منصة التداول:", reply_markup=keyboard)
    await state.clear()

@dp.callback_query(lambda c: c.data and c.data.startswith("select_exchange_"))
async def exchange_selected(callback_query: types.CallbackQuery, state: FSMContext):
    exchange = callback_query.data.replace("select_exchange_", "")
    await state.update_data(exchange=exchange)
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, f"أدخل مفتاح API لمنصة {exchange.capitalize()}:")
    await state.set_state(InvestmentStates.waiting_for_api_key)

@dp.message(state=InvestmentStates.waiting_for_api_key)
async def receive_api_key(message: types.Message, state: FSMContext):
    await state.update_data(api_key=message.text.strip())
    await message.answer("أدخل API Secret:")
    await state.set_state(InvestmentStates.waiting_for_api_secret)

@dp.message(state=InvestmentStates.waiting_for_api_secret)
async def receive_api_secret(message: types.Message, state: FSMContext):
    await state.update_data(api_secret=message.text.strip())
    await message.answer("أدخل Passphrase إن وجد أو أرسل /skip لتخطي:")
    await state.set_state(InvestmentStates.waiting_for_passphrase)

@dp.message(state=InvestmentStates.waiting_for_passphrase)
async def receive_passphrase(message: types.Message, state: FSMContext):
    await state.update_data(passphrase=message.text.strip())
    await save_api_keys(message.from_user.id, state)
    await state.clear()

@dp.message(Command("skip"))
async def skip_passphrase(message: types.Message, state: FSMContext):
    await save_api_keys(message.from_user.id, state)
    await state.clear()

async def save_api_keys(user_telegram_id: int, state: FSMContext):
    data = await state.get_data()
    exchange = data.get('exchange')
    api_key = data.get('api_key')
    api_secret = data.get('api_secret')
    passphrase = data.get('passphrase', None)

    # تحقق من صحة المفاتيح عبر ccxt
    try:
        exchange_class = getattr(ccxt_async, exchange)
        params = {'apiKey': api_key, 'secret': api_secret}
        if passphrase:
            params['password'] = passphrase
        exchange_instance = exchange_class(params)
        await exchange_instance.load_markets()
        await exchange_instance.close()
    except Exception as e:
        await bot.send_message(user_telegram_id, f"خطأ في التحقق من مفاتيح API: {e}\nحاول مرة أخرى.")
        return

    with SessionLocal() as session:
        user = session.query(User).filter_by(telegram_id=user_telegram_id).first()
        if not user:
            user = User(telegram_id=user_telegram_id)
            session.add(user)
            session.commit()
        key_record = session.query(APIKey).filter(and_(
            APIKey.user_id == user.id,
            APIKey.exchange == exchange
        )).first()
        if key_record:
            key_record.api_key_encrypted = safe_encrypt(api_key)
            key_record.api_secret_encrypted = safe_encrypt(api_secret)
            key_record.passphrase_encrypted = safe_encrypt(passphrase) if passphrase else None
            key_record.is_active = True
        else:
            new_key = APIKey(
                user_id=user.id,
                exchange=exchange,
                api_key_encrypted=safe_encrypt(api_key),
                api_secret_encrypted=safe_encrypt(api_secret),
                passphrase_encrypted=safe_encrypt(passphrase) if passphrase else None,
                is_active=True
            )
            session.add(new_key)
        session.commit()
    await bot.send_message(user_telegram_id, f"تم حفظ مفاتيح منصة {exchange.capitalize()} بنجاح.")

# ----- بدء الاستثمار الحقيقي -----

@dp.message(Text("ابدأ استثمار"))
async def start_investment(message: types.Message, state: FSMContext):
    with SessionLocal() as session:
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if not user:
            await message.answer("يرجى تسجيل بيانات التداول أولاً.")
            return
        if not user.is_active:
            await message.answer("الاستثمار معطل لديك.")
            return
    await message.answer("أدخل مبلغ الاستثمار (مثلاً: 1000):", reply_markup=ReplyKeyboardRemove())
    await state.set_state(InvestmentStates.waiting_for_investment_amount)

@dp.message(state=InvestmentStates.waiting_for_investment_amount)
async def process_investment_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.strip())
        if amount <= 0:
            raise ValueError()
    except ValueError:
        await message.answer("أدخل مبلغ صحيح أكبر من صفر.")
        return

    with SessionLocal() as session:
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if not user:
            await message.answer("لم يتم العثور على بياناتك.")
            await state.clear()
            return
        user.investment_amount = amount
        user.is_active = True
        session.commit()

    await message.answer(f"تم تعيين مبلغ الاستثمار: {amount}.\nبدء الاستثمار الآلي الآن...")
    await state.clear()

    # هنا تضيف كود تشغيل استراتيجية المراجحة الفعلية
    asyncio.create_task(run_investment_for_user(user))

async def run_investment_for_user(user: User):
    with SessionLocal() as session:
        api_keys = session.query(APIKey).filter(
            APIKey.user_id == user.id,
            APIKey.is_active == True
        ).all()

    for key in api_keys:
        try:
            exchange_class = getattr(ccxt_async, key.exchange)
            api_key = safe_decrypt(key.api_key_encrypted)
            api_secret = safe_decrypt(key.api_secret_encrypted)
            passphrase = safe_decrypt(key.passphrase_encrypted) if key.passphrase_encrypted else None
            params = {'apiKey': api_key, 'secret': api_secret}
            if passphrase:
                params['password'] = passphrase

            exchange_instance = exchange_class(params)
            await exchange_instance.load_markets()

            # مثال: تنفيذ صفقة مراجحة ذكية بسيطة (تعديل حسب استراتيجيتك)
            symbol = 'BTC/USDT'
            ticker = await exchange_instance.fetch_ticker(symbol)
            price = ticker['last']

            # تنفيذ أمر شراء وهمي (يمكنك تعديلها لتنفيذ فعلي)
            # order = await exchange_instance.create_market_buy_order(symbol, amount)

            await exchange_instance.close()
        except Exception as e:
            print(f"خطأ في تنفيذ الاستثمار: {e}")

# ----- استثمار وهمي -----

@dp.message(Text("استثمار وهمي"))
async def fake_investment(message: types.Message):
    await message.answer("استثمار وهمي يعمل على محاكاة المراجحة باستخدام بيانات حقيقية بدون أموال حقيقية.")

# ----- كشف حساب عن فترة -----

def generate_date_keyboard(start_date: datetime.date, end_date: datetime.date):
    days = (end_date - start_date).days
    keyboard = InlineKeyboardMarkup(row_width=4)
    for i in range(days + 1):
        day = start_date + datetime.timedelta(days=i)
        keyboard.insert(InlineKeyboardButton(day.strftime("%Y-%m-%d"), callback_data=f"date_{day.strftime('%Y-%m-%d')}"))
    return keyboard

@dp.message(Text("كشف حساب عن فترة"))
async def ask_report_start_date(message: types.Message, state: FSMContext):
    today = datetime.date.today()
    keyboard = generate_date_keyboard(today - datetime.timedelta(days=30), today)
    await message.answer("اختر تاريخ بداية الفترة:", reply_markup=keyboard)
    await state.set_state(InvestmentStates.waiting_for_report_start_date)

@dp.callback_query(lambda c: c.data and c.data.startswith("date_"))
async def handle_date_selection(callback_query: types.CallbackQuery, state: FSMContext):
    date_str = callback_query.data.replace("date_", "")
    current_state = await state.get_state()

    if current_state == InvestmentStates.waiting_for_report_start_date.state:
        await state.update_data(report_start_date=date_str)
        await bot.send_message(callback_query.from_user.id, f"تم اختيار بداية الفترة: {date_str}\nاختر تاريخ النهاية:")
        start_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        today = datetime.date.today()
        keyboard = generate_date_keyboard(start_date, today)
        await bot.send_message(callback_query.from_user.id, "اختر تاريخ نهاية الفترة:", reply_markup=keyboard)
        await state.set_state(InvestmentStates.waiting_for_report_end_date)

    elif current_state == InvestmentStates.waiting_for_report_end_date.state:
        data = await state.get_data()
        start_date_str = data.get("report_start_date")
        end_date_str = date_str
        start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d").date()

        if end_date < start_date:
            await bot.send_message(callback_query.from_user.id, "تاريخ النهاية يجب أن يكون بعد البداية، اختر مرة أخرى.")
            return

        await state.update_data(report_end_date=end_date_str)
        await bot.send_message(callback_query.from_user.id, f"جاري تجهيز كشف الحساب من {start_date_str} إلى {end_date_str} ...", reply_markup=ReplyKeyboardRemove())
        await generate_report(callback_query.from_user.id, start_date, end_date)
        await state.clear()

async def generate_report(user_telegram_id: int, start_date: datetime.date, end_date: datetime.date):
    with SessionLocal() as session:
        user = session.query(User).filter_by(telegram_id=user_telegram_id).first()
        if not user:
            await bot.send_message(user_telegram_id, "لم يتم العثور على بيانات المستخدم.")
            return
        trades = session.query(TradeLog).filter(
            TradeLog.user_id == user.id,
            TradeLog.created_at >= datetime.datetime.combine(start_date, datetime.time.min),
            TradeLog.created_at <= datetime.datetime.combine(end_date, datetime.time.max)
        ).all()

    if not trades:
        await bot.send_message(user_telegram_id, "لا توجد صفقات خلال هذه الفترة.")
        return

    msg = f"كشف حساب من {start_date} إلى {end_date}:\n\n"
    total_profit = 0
    for t in trades:
        date_str = t.created_at.strftime("%Y-%m-%d %H:%M")
        msg += f"{date_str} | {t.exchange} | {t.side} | {t.symbol} | الكمية: {t.qty} | السعر: {t.price} | الربح: {t.profit or 0}\n"
        total_profit += t.profit or 0

    msg += f"\nإجمالي الربح/الخسارة: {total_profit:.2f}"
    await bot.send_message(user_telegram_id, msg)

# ----- تقرير حالة السوق -----

@dp.message(Text("حالة السوق"))
async def market_status_report(message: types.Message):
    with SessionLocal() as session:
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if not user:
            await message.answer("يجب تسجيل منصة واحدة على الأقل لعرض حالة السوق.")
            return
        api_keys = session.query(APIKey).filter(
            APIKey.user_id == user.id,
            APIKey.is_active == True
        ).all()

    if not api_keys:
        await message.answer("يجب تسجيل منصة واحدة على الأقل لعرض حالة السوق.")
        return

    exchanges = {}
    for key in api_keys:
        try:
            exchange_class = getattr(ccxt_async, key.exchange)
            api_key = safe_decrypt(key.api_key_encrypted)
            api_secret = safe_decrypt(key.api_secret_encrypted)
            passphrase = safe_decrypt(key.passphrase_encrypted) if key.passphrase_encrypted else None

            params = {'apiKey': api_key, 'secret': api_secret}
            if passphrase:
                params['password'] = passphrase

            exchange_instance = exchange_class(params)
            exchanges[key.exchange] = exchange_instance
        except Exception as e:
            await message.answer(f"خطأ في تهيئة منصة {key.exchange}: {e}")

    symbol_list = ['BTC/USDT', 'ETH/USDT', 'XRP/USDT']
    report_msg = "تقرير حالة السوق:\n\n"

    for name, exchange in exchanges.items():
        try:
            await exchange.load_markets()
            for symbol in symbol_list:
                if symbol in exchange.markets:
                    ticker = await exchange.fetch_ticker(symbol)
                    report_msg += (
                        f"{name.capitalize()} - {symbol}:\n"
                        f"السعر الحالي: {ticker['last']}\n"
                        f"أعلى سعر اليوم: {ticker['high']}\n"
                        f"أدنى سعر اليوم: {ticker['low']}\n"
                        f"حجم التداول اليومي: {ticker['baseVolume']}\n\n"
                    )
            await exchange.close()
        except Exception as e:
            report_msg += f"خطأ في جلب بيانات {name}: {e}\n\n"

    await message.answer(report_msg)

# ----- إيقاف الاستثمار -----

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

# ----- لوحة تحكم المدير -----

@dp.message(Command("admin_panel"))
async def cmd_admin_panel(message: types.Message):
    if message.from_user.id != int(OWNER_ID):
        await message.answer("غير مصرح لك باستخدام هذه الأوامر.")
        return
    await message.answer("لوحة تحكم المدير:", reply_markup=owner_keyboard)

# ----- بدء polling -----

async def main():
    print("البوت بدأ العمل")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())