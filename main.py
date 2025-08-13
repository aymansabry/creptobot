import os
import asyncio
import logging
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from sqlalchemy import create_engine, Column, Integer, BigInteger, String, Float, DateTime, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker

from binance.client import Client as BinanceClient
from kucoin.client import Market, Trade

# لاحقاً: Bybit/OKX/Kraken/Coinbase SDKs
# from bybit import BybitClient
# from okx import OkxClient
# from krakenex import KrakenClient
# from coinbase.wallet.client import Client as CoinbaseClient

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
    platform_buy = Column(String(50))
    platform_sell = Column(String(50))
    amount = Column(Float)
    price = Column(Float)
    fees = Column(Float)
    bot_fee = Column(Float)
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

# لاحقاً: Bybit/OKX/Kraken/Coinbase clients مشابهة

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

# لاحقاً: دوال تحقق Bybit/OKX/Kraken/Coinbase مشابهة

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

def main_menu_keyboard():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("1️⃣ تسجيل/تعديل بيانات التداول", callback_data="menu_edit_trading_data"),
        InlineKeyboardButton("2️⃣ ابدأ استثمار", callback_data="menu_start_invest"),
        InlineKeyboardButton("3️⃣ استثمار وهمي", callback_data="menu_fake_invest"),
        InlineKeyboardButton("4️⃣ كشف حساب عن فترة", callback_data="menu_report"),
        InlineKeyboardButton("5️⃣ حالة السوق", callback_data="menu_market_status"),
        InlineKeyboardButton("6️⃣ إيقاف الاستثمار", callback_data="menu_stop_invest"),
        InlineKeyboardButton("⚙️ اختبار مفاتيح منصة", callback_data="test_platform_prompt"),
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

@dp.callback_query_handler(lambda c: c.data == "menu_edit_trading_data")
async def menu_edit_trading_data(call: types.CallbackQuery):
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=call.from_user.id).first()
    db.close()
    await call.answer()
    await call.message.edit_text("اختر المنصة لإضافة/تعديل مفاتيح API أو تفعيل/إيقاف:", reply_markup=user_platforms_keyboard(user))

# ----------------- باقي الـ Handlers: تسجيل المفاتيح، بدء الاستثمار، كشف الحساب، حالة السوق -----------------

# ⚡ منطق المراجحة مع الربح المتوقع
async def run_arbitrage_loop(user_telegram_id):
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=user_telegram_id).first()
    if not user or user.investment_status != "started":
        db.close()
        return

    while True:
        db.refresh(user)
        if user.investment_status != "started":
            db.close()
            return

        try:
            binance_client = create_binance_client(user)
            kucoin_market, kucoin_trade = create_kucoin_clients(user)
            # لاحقاً: clients البقية

            active_platforms = []
            if binance_client:
                active_platforms.append("Binance")
            if kucoin_trade:
                active_platforms.append("KuCoin")
            # لاحقاً: بقية المنصات

            if not active_platforms:
                await bot.send_message(user.telegram_id, "❌ لا توجد منصات مفعلة للاستثمار.")
                user.investment_status = "stopped"
                db.add(user)
                db.commit()
                db.close()
                return

            # مثال على المراجحة بين Binance و KuCoin
            binance_price = float(binance_client.get_symbol_ticker(symbol="BTCUSDT")['price']) if binance_client else None
            kucoin_price = float(kucoin_market.get_ticker("BTC-USDT")['price']) if kucoin_market else None

            threshold = 20.0
            amount_to_trade = 0
            if user.investment_amount > 0:
                min_price = min(filter(None, [binance_price, kucoin_price]))
                amount_to_trade = user.investment_amount / min_price if min_price else 0

            trade_type = None
            profit = 0
            fees = 0
            bot_fee = 0

            if binance_price and kucoin_price:
                if binance_price + threshold < kucoin_price:
                    trade_type = "Buy Binance / Sell KuCoin"
                    profit = (kucoin_price - binance_price) * amount_to_trade
                elif kucoin_price + threshold < binance_price:
                    trade_type = "Buy KuCoin / Sell Binance"
                    profit = (binance_price - kucoin_price) * amount_to_trade

            # احتساب رسوم وعمولة البوت (مثال)
            fees = amount_to_trade * 0.001  # رسوم تقريبة لكل منصة
            bot_fee = amount_to_trade * 0.002

            if trade_type:
                await bot.send_message(user.telegram_id,
                    f"💰 فرصة مراجحة:\n{trade_type}\n"
                    f"الكمية: {amount_to_trade:.6f} BTC\n"
                    f"رسوم المنصات: {fees:.6f} BTC\n"
                    f"عمولة البوت: {bot_fee:.6f} BTC\n"
                    f"الربح المتوقع: {profit - fees - bot_fee:.6f} BTC"
                )
                # لاحقاً: تنفيذ الصفقة بعد تأكيد العميل

                trade_log = TradeLog(
                    user_id=user.id,
                    trade_type=trade_type,
                    platform_buy=trade_type.split("/")[0].split()[1],
                    platform_sell=trade_type.split("/")[1].split()[1],
                    amount=amount_to_trade,
                    price=min_price,
                    fees=fees,
                    bot_fee=bot_fee,
                    profit=profit - fees - bot_fee
                )
                db.add(trade_log)
                db.commit()

        except Exception as e:
            await bot.send_message(user.telegram_id, f"❌ خطأ في المراجحة: {str(e)}")

        await asyncio.sleep(60)

# ----------------------- RUN BOT -----------------------

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
