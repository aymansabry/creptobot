import os
import asyncio
import logging
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from binance.client import Client as BinanceClient
from kucoin.client import Market, Trade

logging.basicConfig(level=logging.INFO)

# --- البيئة والمتغيرات ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # حاليا مش مستخدم لكن جاهز للتطوير مستقبلاً
DATABASE_URL = os.getenv("DATABASE_URL")

if not BOT_TOKEN or not DATABASE_URL:
    raise Exception("❌ Missing environment variables: BOT_TOKEN, DATABASE_URL")

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# --- موديل قاعدة البيانات ---
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, index=True)
    is_admin = Column(Boolean, default=False)
    binance_api = Column(String(256), nullable=True)
    binance_secret = Column(String(256), nullable=True)
    binance_active = Column(Boolean, default=False)
    kucoin_api = Column(String(256), nullable=True)
    kucoin_secret = Column(String(256), nullable=True)
    kucoin_passphrase = Column(String(256), nullable=True)
    kucoin_active = Column(Boolean, default=False)
    investment_amount = Column(Float, default=0.0)
    investment_status = Column(String(20), default="stopped")  # started / stopped
    profit_percent = Column(Float, default=1.0)  # نسبة الربح للمدير يمكن تعديلها

class TradeLog(Base):
    __tablename__ = "trade_logs"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    trade_type = Column(String(50))
    amount = Column(Float)
    price = Column(Float)
    profit = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(engine)

# --- FSM States ---
class Form(StatesGroup):
    waiting_binance_api = State()
    waiting_binance_secret = State()
    waiting_kucoin_api = State()
    waiting_kucoin_secret = State()
    waiting_kucoin_passphrase = State()
    waiting_investment_amount = State()
    waiting_account_statement_start = State()
    waiting_account_statement_end = State()

# --- قوائم الكيبورد ---

def main_menu(user: User):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("1️⃣ تسجيل أو تعديل بيانات التداول", callback_data="menu_trade_accounts"),
        InlineKeyboardButton("2️⃣ بدء استثمار حقيقي", callback_data="start_invest"),
        InlineKeyboardButton("3️⃣ استثمار وهمي", callback_data="demo_invest"),
        InlineKeyboardButton("4️⃣ كشف حساب عن فترة", callback_data="account_statement"),
        InlineKeyboardButton("5️⃣ حالة السوق", callback_data="market_status"),
        InlineKeyboardButton("6️⃣ إيقاف الاستثمار", callback_data="stop_invest"),
    )
    if user.is_admin:
        kb.add(InlineKeyboardButton("⚙️ قائمة المدير", callback_data="menu_admin"))
    return kb

def trading_platforms_menu(user: User):
    kb = InlineKeyboardMarkup(row_width=1)
    # Binance
    if user.binance_api:
        status = "✅ مفعل" if user.binance_active else "❌ معطل"
        kb.add(InlineKeyboardButton(f"Binance {status}", callback_data="toggle_binance"))
        kb.add(InlineKeyboardButton("تعديل Binance", callback_data="edit_binance"))
    else:
        kb.add(InlineKeyboardButton("ربط Binance", callback_data="link_binance"))
    # KuCoin
    if user.kucoin_api:
        status = "✅ مفعل" if user.kucoin_active else "❌ معطل"
        kb.add(InlineKeyboardButton(f"KuCoin {status}", callback_data="toggle_kucoin"))
        kb.add(InlineKeyboardButton("تعديل KuCoin", callback_data="edit_kucoin"))
    else:
        kb.add(InlineKeyboardButton("ربط KuCoin", callback_data="link_kucoin"))

    kb.add(InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu"))
    return kb

def confirm_toggle_platform_menu(platform_name, enabled: bool):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✅ نعم", callback_data=f"confirm_toggle_{platform_name}_yes"),
        InlineKeyboardButton("❌ لا", callback_data=f"confirm_toggle_{platform_name}_no"),
    )
    return kb

def admin_menu():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("تعديل نسبة ربح البوت", callback_data="admin_edit_profit"),
        InlineKeyboardButton("عدد المستخدمين الإجمالي", callback_data="admin_total_users"),
        InlineKeyboardButton("عدد المستخدمين أونلاين", callback_data="admin_online_users"),
        InlineKeyboardButton("تقارير الاستثمار عن فترة", callback_data="admin_investment_reports"),
        InlineKeyboardButton("حالة البوت البرمجية", callback_data="admin_bot_status"),
        InlineKeyboardButton("التداول كمستخدم عادي", callback_data="admin_trade_as_user"),
        InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu"),
    )
    return kb

# --- دوال مساعدة ---

def create_binance_client(user: User):
    if user.binance_api and user.binance_secret:
        return BinanceClient(user.binance_api, user.binance_secret)
    return None

def create_kucoin_clients(user: User):
    if user.kucoin_api and user.kucoin_secret and user.kucoin_passphrase:
        market_client = Market()
        trade_client = Trade(user.kucoin_api, user.kucoin_secret, user.kucoin_passphrase)
        return market_client, trade_client
    return None, None

async def check_binance_keys(api_key, secret_key):
    try:
        client = BinanceClient(api_key, secret_key)
        client.get_account()
        return True, None
    except Exception as e:
        return False, str(e)

async def check_kucoin_keys(api_key, secret_key, passphrase):
    try:
        trade_client = Trade(api_key, secret_key, passphrase)
        trade_client.get_account()
        return True, None
    except Exception as e:
        return False, str(e)

async def get_wallet_balance_binance(client):
    try:
        account = client.get_account()
        for asset in account['balances']:
            if asset['asset'] == 'USDT':
                return float(asset['free'])
    except:
        return 0.0
    return 0.0

async def get_wallet_balance_kucoin(trade_client):
    try:
        account_info = trade_client.get_account()
        for coin in account_info:
            if coin['currency'] == 'USDT':
                return float(coin['available'])
    except:
        return 0.0
    return 0.0

# --- أوامر وبوت handlers ---

@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
    if not user:
        user = User(telegram_id=message.from_user.id)
        # إذا تريد تحدد admins (مثلاً صاحبك)، ممكن تضيف هنا شرط
        # if message.from_user.id == 123456789:
        #    user.is_admin = True
        db.add(user)
        db.commit()
    await message.answer("أهلاً بك في بوت الاستثمار! اختر من القائمة:", reply_markup=main_menu(user))
    db.close()

@dp.callback_query_handler(lambda c: c.data == "main_menu")
async def go_main_menu(call: types.CallbackQuery):
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=call.from_user.id).first()
    if not user:
        await call.message.edit_text("❌ لم يتم العثور على حسابك. استخدم /start للبدء.")
        db.close()
        return
    await call.message.edit_text("أهلاً بك في بوت الاستثمار! اختر من القائمة:", reply_markup=main_menu(user))
    await call.answer()
    db.close()

# --- قائمة تسجيل أو تعديل بيانات التداول ---
@dp.callback_query_handler(lambda c: c.data == "menu_trade_accounts")
async def trade_accounts_menu(call: types.CallbackQuery):
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=call.from_user.id).first()
    await call.message.edit_text("اختر منصة للتسجيل/التعديل:", reply_markup=trading_platforms_menu(user))
    await call.answer()
    db.close()

# --- ربط Binance ---
@dp.callback_query_handler(lambda c: c.data == "link_binance")
async def link_binance(call: types.CallbackQuery):
    await call.message.answer("🔑 أرسل مفتاح API الخاص بـ Binance:")
    await Form.waiting_binance_api.set()
    await call.answer()

@dp.message_handler(state=Form.waiting_binance_api)
async def process_binance_api(message: types.Message, state: FSMContext):
    await state.update_data(binance_api=message.text)
    await message.answer("🗝️ أرسل Secret Key الخاص بـ Binance:")
    await Form.waiting_binance_secret.set()

@dp.message_handler(state=Form.waiting_binance_secret)
async def process_binance_secret(message: types.Message, state: FSMContext):
    data = await state.get_data()
    api_key = data["binance_api"]
    secret_key = message.text

    valid, err = await check_binance_keys(api_key, secret_key)
    if valid:
        db = SessionLocal()
        user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
        user.binance_api = api_key
        user.binance_secret = secret_key
        user.binance_active = True
        db.add(user)
        db.commit()
        db.close()
        await message.answer("✅ تم ربط Binance بنجاح ✅")
    else:
        await message.answer(f"❌ فشل التحقق من مفاتيح Binance:\n{err}\nأرسل /menu_trade_accounts وحاول مرة أخرى.")

    await state.finish()

# --- ربط KuCoin ---
@dp.callback_query_handler(lambda c: c.data == "link_kucoin")
async def link_kucoin(call: types.CallbackQuery):
    await call.message.answer("🔑 أرسل مفتاح API الخاص بـ KuCoin:")
    await Form.waiting_kucoin_api.set()
    await call.answer()

@dp.message_handler(state=Form.waiting_kucoin_api)
async def process_kucoin_api(message: types.Message, state: FSMContext):
    await state.update_data(kucoin_api=message.text)
    await message.answer("🗝️ أرسل Secret Key الخاص بـ KuCoin:")
    await Form.waiting_kucoin_secret.set()

@dp.message_handler(state=Form.waiting_kucoin_secret)
async def process_kucoin_secret(message: types.Message, state: FSMContext):
    await state.update_data(kucoin_secret=message.text)
    await message.answer("🔐 أرسل Passphrase الخاص بـ KuCoin:")
    await Form.waiting_kucoin_passphrase.set()

@dp.message_handler(state=Form.waiting_kucoin_passphrase)
async def process_kucoin_passphrase(message: types.Message, state: FSMContext):
    data = await state.get_data()
    api_key = data["kucoin_api"]
    secret_key = data["kucoin_secret"]
    passphrase = message.text

    valid, err = await check_kucoin_keys(api_key, secret_key, passphrase)
    if valid:
        db = SessionLocal()
        user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
        user.kucoin_api = api_key
        user.kucoin_secret = secret_key
        user.kucoin_passphrase = passphrase
        user.kucoin_active = True
        db.add(user)
        db.commit()
        db.close()
        await message.answer("✅ تم ربط KuCoin بنجاح ✅")
    else:
        await message.answer(f"❌ فشل التحقق من مفاتيح KuCoin:\n{err}\nأرسل /menu_trade_accounts وحاول مرة أخرى.")
    await state.finish()

# --- تعديل أو تعطيل المنصات ---

@dp.callback_query_handler(lambda c: c.data == "toggle_binance")
async def toggle_binance(call: types.CallbackQuery):
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=call.from_user.id).first()
    new_status = not user.binance_active
    # نطلب تأكيد من المستخدم
    await call.message.edit_text(
        f"هل تريد {'تفعيل' if new_status else 'تعطيل'} Binance؟",
        reply_markup=confirm_toggle_platform_menu("binance", new_status)
    )
    await call.answer()
    db.close()

@dp.callback_query_handler(lambda c: c.data.startswith("confirm_toggle_binance_"))
async def confirm_toggle_binance(call: types.CallbackQuery):
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=call.from_user.id).first()
    if call.data.endswith("_yes"):
        user.binance_active = not user.binance_active
        db.add(user)
        db.commit()
        await call.message.edit_text(f"تم {'تفعيل' if user.binance_active else 'تعطيل'} Binance بنجاح!")
    else:
        await call.message.edit_text("تم إلغاء العملية.")
    db.close()

@dp.callback_query_handler(lambda c: c.data == "toggle_kucoin")
async def toggle_kucoin(call: types.CallbackQuery):
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=call.from_user.id).first()
    new_status = not user.kucoin_active
    await call.message.edit_text(
        f"هل تريد {'تفعيل' if new_status else 'تعطيل'} KuCoin؟",
        reply_markup=confirm_toggle_platform_menu("kucoin", new_status)
    )
    await call.answer()
    db.close()

@dp.callback_query_handler(lambda c: c.data.startswith("confirm_toggle_kucoin_"))
async def confirm_toggle_kucoin(call: types.CallbackQuery):
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=call.from_user.id).first()
    if call.data.endswith("_yes"):
        user.kucoin_active = not user.kucoin_active
        db.add(user)
        db.commit()
        await call.message.edit_text(f"تم {'تفعيل' if user.kucoin_active else 'تعطيل'} KuCoin بنجاح!")
    else:
        await call.message.edit_text("تم إلغاء العملية.")
    db.close()

# --- تعديل بيانات منصات (مكرر لنفس الواجهة) ---
@dp.callback_query_handler(lambda c: c.data in ["edit_binance", "edit_kucoin"])
async def edit_platform(call: types.CallbackQuery):
    platform = call.data.replace("edit_", "")
    await call.message.answer(f"🔑 أرسل مفتاح API الخاص بـ {platform.capitalize()}:")
    if platform == "binance":
        await Form.waiting_binance_api.set()
    elif platform == "kucoin":
        await Form.waiting_kucoin_api.set()
    await call.answer()

# --- تحديد مبلغ الاستثمار ---
@dp.callback_query_handler(lambda c: c.data == "set_investment")
async def set_investment_command(call: types.CallbackQuery):
    await call.message.answer("💰 أرسل مبلغ الاستثمار بالدولار (مثلاً: 100):")
    await Form.waiting_investment_amount.set()
    await call.answer()

@dp.message_handler(state=Form.waiting_investment_amount)
async def process_investment_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text)
        if amount <= 0:
            raise ValueError()
    except:
        await message.answer("❌ المبلغ غير صالح. أرسل رقماً أكبر من صفر.")
        return

    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=message.from_user.id).first()

    # تحقق الرصيد على كل منصة مفعلة (مبسّط، نأخذ الحد الأدنى)
    balances = []
    if user.binance_active:
        client = create_binance_client(user)
        if client:
            balance = await get_wallet_balance_binance(client)
            balances.append(balance)
    if user.kucoin_active:
        _, trade_client = create_kucoin_clients(user)
        if trade_client:
            balance = await get_wallet_balance_kucoin(trade_client)
            balances.append(balance)
    available_balance = min(balances) if balances else 0.0

    if available_balance < amount:
        await message.answer(
            f"❌ رصيدك الحالي {available_balance:.2f} USDT لا يكفي للاستثمار بهذا المبلغ.\n"
            "يرجى إيداع رصيد ثم المحاولة مجددًا."
        )
        await state.finish()
        db.close()
        return

    user.investment_amount = amount
    db.add(user)
    db.commit()
    db.close()

    await message.answer(f"✅ تم تحديد مبلغ الاستثمار: {amount} USDT")
    await state.finish()

# --- بدء الاستثمار الحقيقي ---
@dp.callback_query_handler(lambda c: c.data == "start_invest")
async def start_invest(call: types.CallbackQuery):
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=call.from_user.id).first()
    if not user:
        await call.message.answer("❌ لم يتم ر
