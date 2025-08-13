# -*- coding: utf-8 -*-
import os
import asyncio
import logging
import json
from datetime import datetime

from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, BigInteger, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship

# استخدام النسخة ال async من ccxt
import ccxt.async_support as ccxt

from cryptography.fernet import Fernet, InvalidToken
from openai import OpenAI

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

if not all([BOT_TOKEN, DATABASE_URL, OPENAI_API_KEY, ENCRYPTION_KEY]):
    raise Exception("❌ Missing environment variables.")

openai_client = OpenAI(api_key=OPENAI_API_KEY)
cipher_suite = Fernet(ENCRYPTION_KEY.encode())

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# --- Database setup ---
Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, index=True)
    api_keys = Column(String(500), default="{}")
    investment_amount = Column(Float, default=0.0)
    investment_status = Column(String(20), default="stopped")
    profit_share_owed = Column(Float, default=0.0)
    max_daily_loss = Column(Float, default=0.0)
    current_daily_loss = Column(Float, default=0.0)
    trade_pairs = Column(String(500), default="[]")
    min_profit_percentage = Column(Float, default=0.5)

    trade_logs = relationship("TradeLog", back_populates="user")

    @property
    def get_api_keys(self):
        try:
            decrypted_keys = cipher_suite.decrypt(self.api_keys.encode()).decode()
            return json.loads(decrypted_keys)
        except (InvalidToken, json.JSONDecodeError, UnicodeDecodeError):
            return {}

    @get_api_keys.setter
    def set_api_keys(self, keys_dict):
        encrypted_keys = cipher_suite.encrypt(json.dumps(keys_dict).encode()).decode()
        self.api_keys = encrypted_keys

    def is_api_keys_valid(self):
        try:
            self.get_api_keys
            return True
        except:
            return False

class TradeLog(Base):
    __tablename__ = "trade_logs"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    trade_type = Column(String(50))
    amount = Column(Float)
    profit = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="trade_logs")

Base.metadata.create_all(engine)

# --- FSM ---
class Form(StatesGroup):
    waiting_api_key = State()
    waiting_secret_key = State()
    waiting_passphrase = State()
    waiting_platform = State()
    waiting_investment_amount = State()
    waiting_min_profit = State()
    waiting_max_daily_loss = State()
    waiting_trade_pairs = State()

# --- Helper functions ---
def get_main_menu_keyboard(is_admin=False):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("1️⃣ إعدادات التداول", callback_data="menu_settings"),
        InlineKeyboardButton("2️⃣ ابدأ الاستثمار", callback_data="menu_start_invest"),
        InlineKeyboardButton("3️⃣ كشف حساب", callback_data="menu_report"),
        InlineKeyboardButton("4️⃣ حالة السوق", callback_data="menu_market_status"),
        InlineKeyboardButton("5️⃣ إيقاف الاستثمار", callback_data="menu_stop_invest"),
    )
    if is_admin:
        kb.add(InlineKeyboardButton("⚙️ لوحة تحكم المدير", callback_data="menu_admin_panel"))
    return kb

def get_settings_keyboard(user: User):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("ربط/تعديل مفاتيح API", callback_data="settings_api_keys"),
        InlineKeyboardButton("تحديد مبلغ الاستثمار", callback_data="settings_investment_amount"),
        InlineKeyboardButton("تفعيل/إيقاف المنصات", callback_data="settings_toggle_platforms"),
        InlineKeyboardButton("تحديد أزواج العملات", callback_data="settings_trade_pairs"),
        InlineKeyboardButton("الحد الأدنى للربح", callback_data="settings_min_profit"),
        InlineKeyboardButton("الحد الأقصى للخسارة", callback_data="settings_max_loss"),
        InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu")
    )
    return kb

def get_platforms_keyboard(user: User):
    kb = InlineKeyboardMarkup(row_width=2)
    platforms = ['binance', 'kucoin', 'okx', 'bybit', 'gateio']
    user_keys = user.get_api_keys
    for platform in platforms:
        status_text = "✅" if user_keys.get(platform, {}).get('active', False) else "❌"
        link_status = "(مربوط)" if platform in user_keys else "(غير مربوط)"
        kb.add(InlineKeyboardButton(f"{status_text} {platform.capitalize()} {link_status}", callback_data=f"toggle_platform_{platform}"))
    kb.add(InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu"))
    return kb

# --- Async ccxt helpers ---
async def create_exchange_client(user_api_keys, platform_name):
    platform_info = user_api_keys.get(platform_name)
    if not platform_info:
        return None
    try:
        if platform_name in ['kucoin', 'okx', 'bybit'] and 'passphrase' in platform_info:
            exchange = getattr(ccxt, platform_name)({
                'apiKey': platform_info['key'],
                'secret': platform_info['secret'],
                'password': platform_info['passphrase'],
            })
        else:
            exchange = getattr(ccxt, platform_name)({
                'apiKey': platform_info['key'],
                'secret': platform_info['secret'],
            })
        await exchange.load_markets()
        return exchange
    except Exception as e:
        logging.error(f"Error creating client for {platform_name}: {e}")
        return None

async def verify_exchange_keys(platform_name, api_key, secret_key, passphrase=None):
    try:
        if platform_name in ['kucoin', 'okx', 'bybit'] and passphrase:
            exchange = getattr(ccxt, platform_name)({
                'apiKey': api_key,
                'secret': secret_key,
                'password': passphrase,
            })
        else:
            exchange = getattr(ccxt, platform_name)({
                'apiKey': api_key,
                'secret': secret_key,
            })
        await asyncio.wait_for(exchange.load_markets(), timeout=10)
        await exchange.close()
        return True
    except Exception as e:
        logging.error(f"Failed to verify {platform_name} keys: {e}")
        return False

# --- Handlers (start/menu) ---
@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    with SessionLocal() as db:
        user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
        if not user:
            user = User(telegram_id=message.from_user.id)
            db.add(user)
            db.commit()
        if not user.is_api_keys_valid():
            user.set_api_keys = {}
            db.commit()
            await message.answer("⚠️ تم إعادة ضبط مفاتيح API تلقائيًا.")
    await message.answer("أهلاً بك في بوت المراجحة، اختر من القائمة:", reply_markup=get_main_menu_keyboard())

# --- OpenAI Market Analysis ---
async def get_market_analysis():
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful crypto market analyst."},
                {"role": "user", "content": "اعطني ملخص تحليل سوق العملات الرقمية الحالي مع بعض العملات الرئيسية."}
            ],
            max_tokens=300,
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ خطأ في جلب تحليل السوق: {str(e)}"

@dp.callback_query_handler(lambda c: c.data == "menu_market_status")
async def market_status_handler(call: types.CallbackQuery):
    await call.answer()
    await call.message.edit_text("⏳ جاري تحليل السوق، يرجى الانتظار...")
    analysis_text = await get_market_analysis()
    await call.message.edit_text(analysis_text, reply_markup=get_main_menu_keyboard())

# --- Run Bot ---
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
