import os
import asyncio
import logging
from datetime import datetime

from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import openai
from binance.client import Client as BinanceClient
from kucoin.client import Market, Trade

logging.basicConfig(level=logging.INFO)

# قراءة المتغيرات البيئية
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

if not BOT_TOKEN or not OPENAI_API_KEY or not DATABASE_URL:
    raise Exception("❌ Missing environment variables: BOT_TOKEN, OPENAI_API_KEY, DATABASE_URL")

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

openai.api_key = OPENAI_API_KEY

# --- تعريف جداول قاعدة البيانات ---
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, index=True)
    binance_api = Column(String(256), nullable=True)
    binance_secret = Column(String(256), nullable=True)
    kucoin_api = Column(String(256), nullable=True)
    kucoin_secret = Column(String(256), nullable=True)
    kucoin_passphrase = Column(String(256), nullable=True)
    investment_amount = Column(Float, default=0.0)
    investment_status = Column(String(20), default="stopped")  # started / stopped

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

# --- حالات FSM ---
class Form(StatesGroup):
    waiting_binance_api = State()
    waiting_binance_secret = State()
    waiting_kucoin_api = State()
    waiting_kucoin_secret = State()
    waiting_kucoin_passphrase = State()
    waiting_investment_amount = State()

# --- دوال مساعدة لإنشاء عملاء API ---
def create_binance_client(user: User):
    return BinanceClient(user.binance_api, user.binance_secret)

def create_kucoin_clients(user: User):
    market_client = Market()
    trade_client = Trade(user.kucoin_api, user.kucoin_secret, user.kucoin_passphrase)
    return market_client, trade_client

# --- أوامر بوت ---

@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
    if not user:
        user = User(telegram_id=message.from_user.id)
        db.add(user)
        db.commit()
    db.close()
    await message.answer("أهلاً! استخدم الأوامر لربط حساباتك وبدء الاستثمار:\n"
                         "/link_binance - ربط حساب Binance\n"
                         "/link_kucoin - ربط حساب KuCoin\n"
                         "/set_investment - تحديد مبلغ الاستثمار\n"
                         "/start_invest - بدء الاستثمار\n"
                         "/stop_invest - إيقاف الاستثمار\n"
                         "/status - حالة الاستثمار")

# ربط Binance
@dp.message_handler(commands=["link_binance"])
async def cmd_link_binance(message: types.Message):
    await message.answer("🔑 أرسل مفتاح API الخاص بـ Binance:")
    await Form.waiting_binance_api.set()

@dp.message_handler(state=Form.waiting_binance_api)
async def process_binance_api(message: types.Message, state: FSMContext):
    await state.update_data(binance_api=message.text)
    await message.answer("🗝️ أرسل Secret Key الخاص بـ Binance:")
    await Form.waiting_binance_secret.set()

@dp.message_handler(state=Form.waiting_binance_secret)
async def process_binance_secret(message: types.Message, state: FSMContext):
    data = await state.get_data()
    binance_api = data["binance_api"]
    binance_secret = message.text

    # تحقق سريع من صحة المفاتيح (اختياري)
    try:
        client = BinanceClient(binance_api, binance_secret)
        client.get_account()  # اختبار الاتصال
    except Exception as e:
        await message.answer(f"❌ فشل التحقق من مفاتيح Binance: {e}\nأرسل /link_binance وحاول مرة أخرى.")
        await state.finish()
        return

    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
    user.binance_api = binance_api
    user.binance_secret = binance_secret
    db.add(user)
    db.commit()
    db.close()

    await state.finish()
    await message.answer("✅ تم ربط Binance بنجاح!")

# ربط KuCoin
@dp.message_handler(commands=["link_kucoin"])
async def cmd_link_kucoin(message: types.Message):
    await message.answer("🔑 أرسل مفتاح API الخاص بـ KuCoin:")
    await Form.waiting_kucoin_api.set()

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
    kucoin_api = data["kucoin_api"]
    kucoin_secret = data["kucoin_secret"]
    kucoin_passphrase = message.text

    # تحقق من صحة المفاتيح (اختياري)
    try:
        trade_client = Trade(kucoin_api, kucoin_secret, kucoin_passphrase)
        trade_client.get_account()  # اختبار الاتصال
    except Exception as e:
        await message.answer(f"❌ فشل التحقق من مفاتيح KuCoin: {e}\nأرسل /link_kucoin وحاول مرة أخرى.")
        await state.finish()
        return

    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
    user.kucoin_api = kucoin_api
    user.kucoin_secret = kucoin_secret
    user.kucoin_passphrase = kucoin_passphrase
    db.add(user)
    db.commit()
    db.close()

    await state.finish()
    await message.answer("✅ تم ربط KuCoin بنجاح!")

# تحديد مبلغ الاستثمار
@dp.message_handler(commands=["set_investment"])
async def cmd_set_investment(message: types.Message):
    await message.answer("💰 أرسل مبلغ الاستثمار بالدولار (مثلاً: 100):")
    await Form.waiting_investment_amount.set()

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
    user.investment_amount = amount
    db.add(user)
    db.commit()
    db.close()

    await state.finish()
    await message.answer(f"✅ تم تحديد مبلغ الاستثمار: {amount} USDT")

# بدء الاستثمار
@dp.message_handler(commands=["start_invest"])
async def cmd_start_invest(message: types.Message):
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
    if not user:
        await message.answer("❌ لم يتم ربط حسابك بعد. استخدم /start للبدء.")
        db.close()
        return
    if user.investment_amount <= 0:
        await message.answer("❌ لم يتم تحديد مبلغ الاستثمار بعد. استخدم /set_investment.")
        db.close()
        return

    user.investment_status = "started"
    db.add(user)
    db.commit()
    db.close()

    await message.answer("🚀 بدء الاستثمار والمراجحة...")

    # تشغيل المراجحة في الخلفية
    asyncio.create_task(run_arbitrage_loop(message.from_user.id))

# إيقاف الاستثمار
@dp.message_handler(commands=["stop_invest"])
async def cmd_stop_invest(message: types.Message):
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
    if not user:
        await message.answer("❌ لم يتم ربط حسابك بعد.")
        db.close()
        return

    user.investment_status = "stopped"
    db.add(user)
    db.commit()
    db.close()
    await message.answer("⏹️ تم إيقاف الاستثمار.")

# حالة الاستثمار
@dp.message_handler(commands=["status"])
async def cmd_status(message: types.Message):
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
    if not user:
        await message.answer("❌ لم يتم ربط حسابك بعد.")
        db.close()
        return

    text = (f"📊 حالة استثمارك:\n"
            f"- Binance API: {'مربوط' if user.binance_api else 'غير مربوط'}\n"
            f"- KuCoin API: {'مربوط' if user.kucoin_api else 'غير مربوط'}\n"
            f"- مبلغ الاستثمار: {user.investment_amount} USDT\n"
            f"- حالة الاستثمار: {user.investment_status}")

    await message.answer(text)
    db.close()

# --- حلقة المراجحة التلقائية ---
async def run_arbitrage_loop(user_telegram_id):
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=user_telegram_id).first()
    if not user or user.investment_status != "started":
        db.close()
        return

    while user.investment_status == "started":
        try:
            binance_client = create_binance_client(user)
            kucoin_market, kucoin_trade = create_kucoin_clients(user)

            binance_price = float(binance_client.get_symbol_ticker(symbol="BTCUSDT")['price'])
            kucoin_price = float(kucoin_market.get_ticker("BTC-USDT")['price'])

            threshold = 20  # الحد الأدنى للفرق بالدولار لاعتبارها فرصة

            amount_to_trade = user.investment_amount / min(binance_price, kucoin_price)

            if binance_price + threshold < kucoin_price:
                # شراء من Binance وبيع في KuCoin
                binance_client.order_market_buy(symbol="BTCUSDT", quantity=amount_to_trade)
                kucoin_trade.create_market_order('BTC-USDT', 'sell', size=str(amount_to_trade))
                profit = (kucoin_price - binance_price) * amount_to_trade
                trade_type = "Buy Binance / Sell KuCoin"
            elif kucoin_price + threshold < binance_price:
                # شراء من KuCoin وبيع في Binance
                kucoin_trade.create_market_order('BTC-USDT', 'buy', size=str(amount_to_trade))
                binance_client.order_market_sell(symbol="BTCUSDT", quantity=amount_to_trade)
                profit = (binance_price - kucoin_price) * amount_to_trade
                trade_type = "Buy KuCoin / Sell Binance"
            else:
                profit = 0
                trade_type = None

            if trade_type:
                # تسجيل الصفقة
                trade = TradeLog(
                    user_id=user.id,
                    trade_type=trade_type,
                    amount=amount_to_trade,
                    price=min(binance_price, kucoin_price),
                    profit=profit
                )
                db.add(trade)
                db.commit()

                await bot.send_message(user.telegram_id,
                    f"✅ تمت عملية المراجحة:\n{trade_type}\nالكمية: {amount_to_trade:.6f} BTC\nالربح المتوقع: {profit:.2f} USDT")
            else:
                await bot.send_message(user.telegram_id, "⚠️ لا توجد فرص مراجحة حالياً.")

            db.refresh(user)
            await asyncio.sleep(30)  # تأخير 30 ثانية قبل المحاولة القادمة

        except Exception as e:
            await bot.send_message(user.telegram_id, f"❌ خطأ أثناء المراجحة: {str(e)}")
            await asyncio.sleep(60)

    db.close()

# تشغيل البوت
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
