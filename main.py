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
from sqlalchemy.orm import declarative_base, sessionmaker

from binance.client import Client as BinanceClient
from kucoin.client import Market, Trade  # حذف Client لأنها غير موجودة في المكتبة الحديثة

import openai

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not BOT_TOKEN or not DATABASE_URL or not OPENAI_API_KEY:
    raise Exception("❌ Missing environment variables BOT_TOKEN or DATABASE_URL or OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# ----------------------- DB MODELS -----------------------

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, index=True)
    # API keys per platform
    binance_api = Column(String(256), nullable=True)
    binance_secret = Column(String(256), nullable=True)
    kucoin_api = Column(String(256), nullable=True)
    kucoin_secret = Column(String(256), nullable=True)
    kucoin_passphrase = Column(String(256), nullable=True)
    # Investment info
    investment_amount = Column(Float, default=0.0)
    investment_status = Column(String(20), default="stopped")  # started / stopped
    # Store which platforms are active
    binance_active = Column(Boolean, default=False)
    kucoin_active = Column(Boolean, default=False)

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

# ----------------------- FSM States -----------------------

class Form(StatesGroup):
    platform_choice = State()
    waiting_api_key = State()
    waiting_secret_key = State()
    waiting_passphrase = State()
    waiting_investment_amount = State()
    waiting_report_start = State()
    waiting_report_end = State()
    confirm_invest = State()

# ----------------------- HELPERS -----------------------

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

async def verify_binance_keys(api_key, secret_key):
    try:
        client = BinanceClient(api_key, secret_key)
        client.get_account()
        return True
    except Exception:
        return False

async def verify_kucoin_keys(api_key, secret_key, passphrase):
    try:
        client = Trade(api_key, secret_key, passphrase)  # استخدم Trade للتحقق من المفاتيح
        accounts = client.get_accounts()
        return bool(accounts)
    except Exception:
        return False

def user_platforms_keyboard(user: User):
    kb = InlineKeyboardMarkup(row_width=2)
    binance_text = ("✅ Binance" if user.binance_active else "❌ Binance") + (" (مربوط)" if user.binance_api else " (غير مربوط)")
    kucoin_text = ("✅ KuCoin" if user.kucoin_active else "❌ KuCoin") + (" (مربوط)" if user.kucoin_api else " (غير مربوط)")
    kb.insert(InlineKeyboardButton(binance_text, callback_data="platform_binance"))
    kb.insert(InlineKeyboardButton(kucoin_text, callback_data="platform_kucoin"))
    kb.add(InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu"))
    return kb

def main_menu_keyboard():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("1️⃣ تسجيل/تعديل بيانات التداول", callback_data="menu_edit_trading_data"),
        InlineKeyboardButton("2️⃣ ابدأ استثمار", callback_data="menu_start_invest"),
        InlineKeyboardButton("3️⃣ استثمار وهمي", callback_data="menu_fake_invest"),
        InlineKeyboardButton("4️⃣ كشف حساب عن فترة", callback_data="menu_report"),
        InlineKeyboardButton("5️⃣ حالة السوق", callback_data="menu_market_status"),
        InlineKeyboardButton("6️⃣ إيقاف الاستثمار", callback_data="menu_stop_invest"),
    )
    return kb

# ----------------------- HANDLERS -----------------------

@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
    if not user:
        user = User(telegram_id=message.from_user.id)
        db.add(user)
        db.commit()
    db.close()

    await message.answer("أهلاً بك في بوت الاستثمار، اختر من القائمة:", reply_markup=main_menu_keyboard())

@dp.callback_query_handler(lambda c: c.data == "main_menu")
async def back_to_main(call: types.CallbackQuery):
    await call.answer()
    await call.message.edit_text("القائمة الرئيسية:", reply_markup=main_menu_keyboard())

# 1- تسجيل/تعديل بيانات التداول
@dp.callback_query_handler(lambda c: c.data == "menu_edit_trading_data")
async def menu_edit_trading_data(call: types.CallbackQuery):
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=call.from_user.id).first()
    db.close()
    await call.answer()
    await call.message.edit_text(
        "اختر المنصة لإضافة/تعديل مفاتيح API أو تفعيل/إيقاف:",
        reply_markup=user_platforms_keyboard(user)
    )

@dp.callback_query_handler(lambda c: c.data.startswith("platform_"))
async def platform_selected(call: types.CallbackQuery, state: FSMContext):
    platform = call.data.split("_")[1]
    await state.update_data(selected_platform=platform)
    await call.answer()

    if platform == "binance":
        await call.message.edit_text("أرسل مفتاح API الخاص بمنصة Binance:")
        await Form.waiting_api_key.set()
    elif platform == "kucoin":
        await call.message.edit_text("أرسل مفتاح API الخاص بمنصة KuCoin:")
        await Form.waiting_api_key.set()

@dp.message_handler(state=Form.waiting_api_key)
async def api_key_received(message: types.Message, state: FSMContext):
    data = await state.get_data()
    platform = data["selected_platform"]
    api_key = message.text.strip()

    await state.update_data(api_key=api_key)

    if platform == "binance":
        await message.answer("أرسل الـ Secret Key الخاص بـ Binance:")
        await Form.waiting_secret_key.set()
    elif platform == "kucoin":
        await message.answer("أرسل الـ Secret Key الخاص بـ KuCoin:")
        await Form.waiting_secret_key.set()

@dp.message_handler(state=Form.waiting_secret_key)
async def secret_key_received(message: types.Message, state: FSMContext):
    data = await state.get_data()
    platform = data["selected_platform"]
    secret_key = message.text.strip()

    await state.update_data(secret_key=secret_key)

    if platform == "binance":
        valid = await verify_binance_keys(data["api_key"], secret_key)
        if not valid:
            await message.answer("❌ المفاتيح غير صحيحة، أرسل /start وحاول مرة أخرى.")
            await state.finish()
            return
        db = SessionLocal()
        user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
        user.binance_api = data["api_key"]
        user.binance_secret = secret_key
        user.binance_active = True
        db.add(user)
        db.commit()
        db.close()
        await message.answer("✅ تم ربط Binance بنجاح!")
        await state.finish()
        await message.answer("العودة للقائمة الرئيسية:", reply_markup=main_menu_keyboard())

    elif platform == "kucoin":
        await message.answer("أرسل الـ Passphrase الخاص بـ KuCoin:")
        await Form.waiting_passphrase.set()

@dp.message_handler(state=Form.waiting_passphrase)
async def passphrase_received(message: types.Message, state: FSMContext):
    data = await state.get_data()
    passphrase = message.text.strip()
    platform = data["selected_platform"]

    valid = await verify_kucoin_keys(data["api_key"], data["secret_key"], passphrase)
    if not valid:
        await message.answer("❌ المفاتيح غير صحيحة أو لا تحتوي على الصلاحيات اللازمة. تأكد من تفعيل صلاحيات القراءة والتداول فقط، وأعد المحاولة.")
        await state.finish()
        return

    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
    user.kucoin_api = data["api_key"]
    user.kucoin_secret = data["secret_key"]
    user.kucoin_passphrase = passphrase
    user.kucoin_active = True
    db.add(user)
    db.commit()
    db.close()

    await message.answer("✅ تم ربط KuCoin بنجاح!")
    await state.finish()
    await message.answer("العودة للقائمة الرئيسية:", reply_markup=main_menu_keyboard())

# باقي الكود كما في السابق، بدون تغييرات جوهرية على الوظائف

# ... (باقي handlers واستثمار وهمي، كشف حساب، حالة السوق، المراجحة، إلخ)

# ----------------------- START BOT -----------------------

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)