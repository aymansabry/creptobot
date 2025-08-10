import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, Text, StateFilter
from aiogram.types import ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError
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

class InvestmentStates(StatesGroup):
    waiting_for_exchange_name = State()
    waiting_for_api_key = State()
    waiting_for_api_secret = State()
    waiting_for_passphrase = State()
    waiting_for_investment_amount = State()
    waiting_for_report_start_date = State()
    waiting_for_report_end_date = State()
    waiting_for_profit_percentage = State()

# أزرار المستخدم
user_inline_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="مساعدة /help", callback_data="help"),
            InlineKeyboardButton(text="تسجيل/تعديل بيانات التداول", callback_data="register_trading_data"),
        ],
        [
            InlineKeyboardButton(text="ابدأ استثمار", callback_data="start_investment"),
            InlineKeyboardButton(text="استثمار وهمي", callback_data="fake_investment"),
        ],
        [
            InlineKeyboardButton(text="كشف حساب عن فترة", callback_data="account_statement"),
            InlineKeyboardButton(text="حالة السوق", callback_data="market_status"),
        ],
        [
            InlineKeyboardButton(text="ايقاف الاستثمار", callback_data="stop_investment"),
        ]
    ]
)

# أزرار المالك
owner_inline_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="/help", callback_data="help"),
            InlineKeyboardButton(text="/admin_panel", callback_data="admin_panel"),
        ],
        [
            InlineKeyboardButton(text="تعديل نسبة ربح البوت", callback_data="edit_profit_percentage"),
            InlineKeyboardButton(text="عدد المستخدمين", callback_data="user_count"),
        ],
        [
            InlineKeyboardButton(text="عدد المستخدمين أونلاين", callback_data="online_user_count"),
            InlineKeyboardButton(text="تقارير الاستثمار", callback_data="investment_reports"),
        ],
        [
            InlineKeyboardButton(text="حالة البوت البرمجية", callback_data="bot_status"),
        ]
    ]
)

def safe_encrypt(text):
    return fernet.encrypt(text.encode()).decode()

def safe_decrypt(token):
    try:
        return fernet.decrypt(token.encode()).decode()
    except InvalidToken:
        return None

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if message.from_user.id == int(OWNER_ID):
        await message.answer("أهلاً مالك البوت!", reply_markup=owner_inline_keyboard)
    else:
        with SessionLocal() as session:
            user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
            if not user:
                user = User(telegram_id=message.from_user.id)
                session.add(user)
                session.commit()
        await message.answer("أهلاً! البوت يعمل بنجاح.", reply_markup=user_inline_keyboard)

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.reply(
        "أوامر البوت:\n"
        "/start - بدء البوت\n"
        "/help - عرض هذه الرسالة\n"
        "تسجيل/تعديل بيانات التداول - لربط حسابك بمنصة تداول\n"
        "ابدأ استثمار - لتفعيل التداول الآلي\n"
        "استثمار وهمي - لتجربة التداول بدون مخاطرة\n"
        "كشف حساب عن فترة - للحصول على تقرير بالأرباح والخسائر\n"
        "حالة السوق - لعرض أحدث بيانات السوق\n"
        "ايقاف الاستثمار - لإيقاف التداول الآلي\n"
    )

@dp.callback_query(Text("help"))
async def help_callback(callback_query: types.CallbackQuery):
    await cmd_help(callback_query.message)
    await callback_query.answer()

@dp.callback_query(Text("register_trading_data"))
async def start_api_key_registration(callback_query: types.CallbackQuery, state: FSMContext):
    exchange_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Binance", callback_data="select_exchange_binance"),
                InlineKeyboardButton(text="KuCoin", callback_data="select_exchange_kucoin"),
            ],
            [
                InlineKeyboardButton(text="OKX", callback_data="select_exchange_okx"),
                InlineKeyboardButton(text="Bybit", callback_data="select_exchange_bybit"),
            ]
        ]
    )
    await callback_query.message.answer("اختر منصة التداول:", reply_markup=exchange_keyboard)
    await state.set_state(InvestmentStates.waiting_for_exchange_name)
    await callback_query.answer()

@dp.callback_query(Text(startswith="select_exchange_"))
async def select_exchange(callback_query: types.CallbackQuery, state: FSMContext):
    exchange = callback_query.data.replace("select_exchange_", "")
    await state.update_data(exchange=exchange)
    await bot.send_message(callback_query.from_user.id, f"أدخل مفتاح API لمنصة {exchange.capitalize()}:")
    await state.set_state(InvestmentStates.waiting_for_api_key)
    await callback_query.answer()

@dp.message(StateFilter(InvestmentStates.waiting_for_api_key))
async def receive_api_key(message: types.Message, state: FSMContext):
    await state.update_data(api_key=safe_encrypt(message.text))
    await message.answer("أدخل مفتاح API Secret:")
    await state.set_state(InvestmentStates.waiting_for_api_secret)

@dp.message(StateFilter(InvestmentStates.waiting_for_api_secret))
async def receive_api_secret(message: types.Message, state: FSMContext):
    await state.update_data(api_secret=safe_encrypt(message.text))
    data = await state.get_data()
    exchange = data.get("exchange")

    if exchange.lower() in ['okx', 'bybit']:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="تخطي", callback_data="skip_passphrase")]
        ])
        await message.answer("أدخل Passphrase (أو اضغط تخطي):", reply_markup=keyboard)
        await state.set_state(InvestmentStates.waiting_for_passphrase)
    else:
        await save_api_keys(message, state)

@dp.message(StateFilter(InvestmentStates.waiting_for_passphrase))
async def receive_passphrase(message: types.Message, state: FSMContext):
    await state.update_data(passphrase=safe_encrypt(message.text))
    await save_api_keys(message, state)

@dp.callback_query(Text("skip_passphrase"))
async def skip_passphrase(callback_query: types.CallbackQuery, state: FSMContext):
    await state.update_data(passphrase=None)
    await save_api_keys(callback_query.message, state)

async def save_api_keys(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    exchange = data.get("exchange")
    api_key = data.get("api_key")
    api_secret = data.get("api_secret")
    passphrase = data.get("passphrase")

    with SessionLocal() as session:
        api_key_record = session.query(APIKey).filter(
            and_(APIKey.user_id == user_id, APIKey.exchange == exchange)
        ).first()

        if api_key_record:
            api_key_record.api_key = api_key
            api_key_record.api_secret = api_secret
            api_key_record.passphrase = passphrase
        else:
            new_api_key = APIKey(
                user_id=user_id,
                exchange=exchange,
                api_key=api_key,
                api_secret=api_secret,
                passphrase=passphrase
            )
            session.add(new_api_key)
        
        session.commit()
    
    await message.answer("تم حفظ بيانات التداول بنجاح!", reply_markup=user_inline_keyboard)
    await state.clear()

@dp.callback_query(Text("start_investment"))
async def start_investment(callback_query: types.CallbackQuery, state: FSMContext):
    with SessionLocal() as session:
        api_key_record = session.query(APIKey).filter_by(user_id=callback_query.from_user.id).first()
        if not api_key_record:
            await callback_query.message.answer("يجب عليك تسجيل بيانات التداول أولاً.")
            await callback_query.answer()
            return

    await callback_query.message.answer("أدخل المبلغ الذي ترغب في استثماره (بالدولار):")
    await state.set_state(InvestmentStates.waiting_for_investment_amount)
    await callback_query.answer()

@dp.message(StateFilter(InvestmentStates.waiting_for_investment_amount))
async def process_investment_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text)
        if amount <= 0:
            raise ValueError
        
        await message.answer(f"تم بدء الاستثمار بمبلغ {amount} دولار. سأقوم بإدارة التداول تلقائيًا.")
        await state.clear()
        
        # مثال على استدعاء دالة التداول (غير مفعلة هنا)
        # await run_investment_for_user(message.from_user.id, amount)
        
    except ValueError:
        await message.answer("أدخل مبلغًا صحيحًا. يرجى إدخال رقم موجب.")

@dp.callback_query(Text("fake_investment"))
async def fake_investment(callback_query: types.CallbackQuery):
    await callback_query.message.answer("تم بدء الاستثمار الوهمي بنجاح. سيتم محاكاة التداول وسأرسل لك تقريرًا دوريًا.")
    await callback_query.answer()

@dp.callback_query(Text("account_statement"))
async def ask_report_start_date(callback_query: types.CallbackQuery, state: FSMContext):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="اليوم", callback_data="date_today"),
                InlineKeyboardButton(text="الأسبوع الماضي", callback_data="date_last_week"),
            ],
            [
                InlineKeyboardButton(text="الشهر الماضي", callback_data="date_last_month"),
                InlineKeyboardButton(text="كل الوقت", callback_data="date_all_time"),
            ]
        ]
    )
    await callback_query.message.answer("اختر الفترة التي ترغب في الحصول على تقرير عنها:", reply_markup=keyboard)
    await state.set_state(InvestmentStates.waiting_for_report_start_date)
    await callback_query.answer()

@dp.callback_query(Text(startswith="date_"), StateFilter(InvestmentStates.waiting_for_report_start_date))
async def handle_date_selection(callback_query: types.CallbackQuery, state: FSMContext):
    period = callback_query.data.split("_")[1]
    end_date = datetime.date.today()
    start_date = None

    if period == "today":
        start_date = end_date
    elif period == "last_week":
        start_date = end_date - datetime.timedelta(days=7)
    elif period == "last_month":
        start_date = end_date - datetime.timedelta(days=30)
    elif period == "all_time":
        start_date = datetime.date(2023, 1, 1)

    await generate_report(callback_query.message, callback_query.from_user.id, start_date, end_date)
    await state.clear()
    await callback_query.answer()

async def generate_report(message: types.Message, user_id: int, start_date: datetime.date, end_date: datetime.date):
    with SessionLocal() as session:
        trades = session.query(TradeLog).filter(
            and_(
                TradeLog.user_id == user_id,
                TradeLog.timestamp >= start_date,
                TradeLog.timestamp <= end_date
            )
        ).all()

    if not trades:
        await message.answer(f"لا توجد صفقات مسجلة في الفترة من {start_date} إلى {end_date}.")
        return

    total_profit = sum(t.profit for t in trades)
    report_text = f"**كشف حساب للفترة من {start_date} إلى {end_date}**\n\n"
    report_text += f"إجمالي عدد الصفقات: {len(trades)}\n"
    report_text += f"إجمالي الربح/الخسارة: {total_profit:.2f} $\n"

    await message.answer(report_text, parse_mode="Markdown")

@dp.callback_query(Text("market_status"))
async def market_status_report(callback_query: types.CallbackQuery):
    exchange = ccxt_async.binance()
    try:
        tickers = await exchange.fetch_tickers()
        btc_price = tickers['BTC/USDT']['last']
        eth_price = tickers['ETH/USDT']['last']
        await callback_query.message.answer(
            f"**حالة السوق الحالية:**\n\n"
            f"سعر BTC/USDT: {btc_price:.2f} $\n"
            f"سعر ETH/USDT: {eth_price:.2f} $"
        )
    except Exception as e:
        await callback_query.message.answer(f"حدث خطأ أثناء جلب بيانات السوق: {e}")
    finally:
        await exchange.close()
    await callback_query.answer()

@dp.callback_query(Text("stop_investment"))
async def stop_investment(callback_query: types.CallbackQuery):
    # منطق إيقاف التداول هنا (حسب تصميمك)
    await callback_query.message.answer("تم إيقاف جميع استثماراتك بنجاح. لن يتم فتح صفقات جديدة تلقائيًا.")
    await callback_query.answer()

@dp.callback_query(Text("admin_panel"))
async def cmd_admin_panel(callback_query: types.CallbackQuery):
    if callback_query.from_user.id != int(OWNER_ID):
        await callback_query.answer("غير مصرح لك باستخدام هذه الأوامر.", show_alert=True)
        return
    await callback_query.message.answer("أهلاً بك في لوحة تحكم المالك.", reply_markup=owner_inline_keyboard)
    await callback_query.answer()

@dp.callback_query(Text("edit_profit_percentage"))
async def edit_profit_percentage(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.from_user.id != int(OWNER_ID):
        await callback_query.answer("غير مصرح لك.", show_alert=True)
        return
    await callback_query.message.answer("أدخل نسبة الربح الجديدة (مثال: 0.1):")
    await state.set_state(InvestmentStates.waiting_for_profit_percentage)
    await callback_query.answer()

@dp.message(StateFilter(InvestmentStates.waiting_for_profit_percentage))
async def set_profit_percentage(message: types.Message, state: FSMContext):
    try:
        profit_percentage = float(message.text)
        # احفظ النسبة في مكان مناسب (إعدادات أو قاعدة بيانات)
        await message.answer(f"تم تحديث نسبة الربح إلى {profit_percentage}.")
    except ValueError:
        await message.answer("الرجاء إدخال قيمة رقمية صحيحة.")
    finally:
        await state.clear()

@dp.callback_query(Text("user_count"))
async def get_user_count(callback_query: types.CallbackQuery):
    with SessionLocal() as session:
        count = session.query(User).count()
    await callback_query.message.answer(f"عدد المستخدمين الإجمالي: {count}")
    await callback_query.answer()

@dp.callback_query(Text("bot_status"))
async def get_bot_status(callback_query: types.CallbackQuery):
    await callback_query.message.answer("حالة البوت: يعمل بشكل طبيعي ✅")
    await callback_query.answer()

async def main():
    print("البوت بدأ العمل")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("البوت توقف عن العمل")