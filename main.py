import os
import asyncio
import logging
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from sqlalchemy import create_engine, Column, BigInteger, Integer, String, Float, DateTime, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker

from binance.client import Client as BinanceClient
from kucoin.client import Market, Trade
# Bybit, OKX, Kraken, Coinbase clients placeholders
# يجب إضافة المكتبات الرسمية لكل منصة لاحقاً

import openai

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not BOT_TOKEN or not DATABASE_URL or not OPENAI_API_KEY:
    raise Exception("❌ Missing environment variables BOT_TOKEN, DATABASE_URL or OPENAI_API_KEY")

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
    telegram_id = Column(BigInteger, unique=True, index=True)
    binance_api = Column(String(512), nullable=True)
    binance_secret = Column(String(512), nullable=True)
    binance_active = Column(Boolean, default=False)
    kucoin_api = Column(String(512), nullable=True)
    kucoin_secret = Column(String(512), nullable=True)
    kucoin_passphrase = Column(String(512), nullable=True)
    kucoin_active = Column(Boolean, default=False)
    bybit_api = Column(String(512), nullable=True)
    bybit_secret = Column(String(512), nullable=True)
    bybit_active = Column(Boolean, default=False)
    okx_api = Column(String(512), nullable=True)
    okx_secret = Column(String(512), nullable=True)
    okx_passphrase = Column(String(512), nullable=True)
    okx_active = Column(Boolean, default=False)
    kraken_api = Column(String(512), nullable=True)
    kraken_secret = Column(String(512), nullable=True)
    kraken_active = Column(Boolean, default=False)
    coinbase_api = Column(String(512), nullable=True)
    coinbase_secret = Column(String(512), nullable=True)
    coinbase_passphrase = Column(String(512), nullable=True)
    coinbase_active = Column(Boolean, default=False)
    investment_amount = Column(Float, default=0.0)
    investment_status = Column(String(20), default="stopped")

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

# ----------------------- FSM STATES -----------------------
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
        trade_client = Trade(api_key, secret_key, passphrase)
        accounts = trade_client.get_accounts()
        return bool(accounts)
    except Exception:
        return False

# ----------------------- KEYBOARDS -----------------------
def main_menu_keyboard():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("1️⃣ تسجيل/تعديل بيانات التداول", callback_data="menu_edit_trading_data"),
        InlineKeyboardButton("2️⃣ ابدأ استثمار", callback_data="menu_start_invest"),
        InlineKeyboardButton("3️⃣ استثمار وهمي", callback_data="menu_fake_invest"),
        InlineKeyboardButton("4️⃣ كشف حساب عن فترة", callback_data="menu_report"),
        InlineKeyboardButton("5️⃣ حالة السوق", callback_data="menu_market_status"),
        InlineKeyboardButton("6️⃣ إيقاف الاستثمار", callback_data="menu_stop_invest"),
        InlineKeyboardButton("⚙️ اختبار مفاتيح KuCoin", callback_data="test_kucoin_prompt"),
    )
    return kb

def user_platforms_keyboard(user: User):
    kb = InlineKeyboardMarkup(row_width=2)
    platforms = [
        ("Binance", user.binance_active, user.binance_api),
        ("KuCoin", user.kucoin_active, user.kucoin_api),
        ("Bybit", user.bybit_active, user.bybit_api),
        ("OKX", user.okx_active, user.okx_api),
        ("Kraken", user.kraken_active, user.kraken_api),
        ("Coinbase", user.coinbase_active, user.coinbase_api),
    ]
    for name, active, api in platforms:
        text = ("✅ " if active else "❌ ") + name + (" (مربوط)" if api else " (غير مربوط)")
        kb.insert(InlineKeyboardButton(text, callback_data=f"platform_{name.lower()}"))
    kb.add(InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu"))
    return kb

# ----------------------- START HANDLER -----------------------
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

# ----------------------- باقي الhandlers -----------------------
# handlers لكل القوائم، المراجحة، التقارير، OpenAI، اختبار مفاتيح KuCoin
# (نفس المنطق الذي سبق وأرسلته، مع التعديلات الجديدة لجميع المنصات)

# ----------------------- RUN BOT -----------------------
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
