import os
import asyncio
import logging
from datetime import datetime

import openai
from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# مكتبات التداول Binance وKuCoin
from binance.client import Client as BinanceClient
from kucoin.client import Client as KuCoinClient

logging.basicConfig(level=logging.INFO)

# قراءة المتغيرات
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN not found.")
if not OPENAI_API_KEY:
    raise ValueError("❌ OPENAI_API_KEY not found.")
if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL not found.")

print("✅ Environment variables loaded.")

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# جداول
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, index=True)
    binance_api = Column(String(256), nullable=True)
    binance_secret = Column(String(256), nullable=True)
    kucoin_api = Column(String(256), nullable=True)
    kucoin_secret = Column(String(256), nullable=True)
    kucoin_passphrase = Column(String(256), nullable=True)
    investment_amount = Column(Float, default=0.0)
    investment_status = Column(String(20), default="stopped")  # started/stopped
    balance = Column(Float, default=0.0)  # لمحفظة المستخدم داخل البوت

class TradeLog(Base):
    __tablename__ = 'trade_logs'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    trade_type = Column(String(20))
    amount = Column(Float)
    price = Column(Float)
    profit = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(engine)

openai.api_key = OPENAI_API_KEY

class Form(StatesGroup):
    waiting_binance_api = State()
    waiting_binance_secret = State()
    waiting_kucoin_api = State()
    waiting_kucoin_secret = State()
    waiting_kucoin_passphrase = State()
    waiting_investment_amount = State()

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.answer(
        "🤖 أهلاً بك في بوت المراجحة الآلية!\n\n"
        "/link_binance - ربط حساب Binance\n"
        "/link_kucoin - ربط حساب KuCoin\n"
        "/set_investment - تحديد مبلغ الاستثمار\n"
        "/start_invest - بدء الاستثمار\n"
        "/stop_invest - إيقاف الاستثمار\n"
        "/status - عرض الحالة"
    )

@dp.message_handler(commands=['link_binance'])
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

    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
    if not user:
        user = User(telegram_id=message.from_user.id)
    user.binance_api = binance_api
    user.binance_secret = binance_secret
    db.add(user)
    db.commit()
    db.close()

    await state.finish()
    await message.answer("✅ تم ربط Binance بنجاح!")

@dp.message_handler(commands=['link_kucoin'])
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

    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
    if not user:
        user = User(telegram_id=message.from_user.id)
    user.kucoin_api = kucoin_api
    user.kucoin_secret = kucoin_secret
    user.kucoin_passphrase = kucoin_passphrase
    db.add(user)
    db.commit()
    db.close()

    await state.finish()
    await message.answer("✅ تم ربط KuCoin بنجاح!")

@dp.message_handler(commands=['set_investment'])
async def cmd_set_investment(message: types.Message):
    await message.answer("💰 أرسل مبلغ الاستثمار (بالـ USDT):")
    await Form.waiting_investment_amount.set()

@dp.message_handler(state=Form.waiting_investment_amount)
async def process_investment_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text)
    except ValueError:
        await message.answer("❌ أرسل رقم صالح.")
        return

    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
    if not user:
        user = User(telegram_id=message.from_user.id)
    user.investment_amount = amount
    db.add(user)
    db.commit()
    db.close()

    await state.finish()
    await message.answer(f"✅ تم تحديد مبلغ الاستثمار: {amount} USDT")

@dp.message_handler(commands=['start_invest'])
async def cmd_start_invest(message: types.Message):
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
    if not user:
        await message.answer("❌ لم يتم ربط حساب تداول.")
        db.close()
        return
    if user.investment_amount <= 0:
        await message.answer("❌ يرجى تحديد مبلغ الاستثمار أولاً.")
        db.close()
        return

    user.investment_status = "started"
    db.commit()
    db.close()

    await message.answer("🚀 تم بدء الاستثمار! المراجحة ستبدأ الآن.")
    asyncio.create_task(run_arbitrage_loop(user.telegram_id))

@dp.message_handler(commands=['stop_invest'])
async def cmd_stop_invest(message: types.Message):
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
    if user:
        user.investment_status = "stopped"
        db.commit()
    db.close()
    await message.answer("🛑 تم إيقاف الاستثمار.")

@dp.message_handler(commands=['status'])
async def cmd_status(message: types.Message):
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
    if user:
        await message.answer(
            f"📊 الحالة: {user.investment_status}\n"
            f"💰 مبلغ الاستثمار: {user.investment_amount} USDT"
        )
    else:
        await message.answer("❌ لا توجد بيانات مسجلة.")
    db.close()

# --- تنفيذ الأوامر على Binance و KuCoin ---

def create_binance_client(user):
    return BinanceClient(user.binance_api, user.binance_secret)

def create_kucoin_client(user):
    return KuCoinClient(user.kucoin_api, user.kucoin_secret, user.kucoin_passphrase)

async def run_arbitrage_loop(user_telegram_id):
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=user_telegram_id).first()
    if not user:
        db.close()
        return

    while user.investment_status == "started":
        try:
            # مثال: تحقق الأسعار من المنصتين (BTCUSDT)
            binance_client = create_binance_client(user)
            kucoin_client = create_kucoin_client(user)

            binance_price = float(binance_client.get_symbol_ticker(symbol="BTCUSDT")['price'])
            kucoin_price = float(kucoin_client.get_ticker("BTC-USDT")['price'])

            await bot.send_message(user.telegram_id, f"📈 أسعار BTCUSDT:\nBinance: {binance_price}\nKuCoin: {kucoin_price}")

            # قرار شراء وبيع بناءً على الفرق
            threshold = 20  # دولار فرق بسيط (يمكن تعديله)
            amount_to_trade = user.investment_amount / min(binance_price, kucoin_price)  # عدد عملة BTC

            if binance_price + threshold < kucoin_price:
                # شراء من باينانس وبيع في كوكوين
                await bot.send_message(user.telegram_id, "🔄 فرصة مراجحة: شراء BTC من Binance وبيع في KuCoin")

                order_binance = binance_client.order_market_buy(symbol="BTCUSDT", quantity=amount_to_trade)
                order_kucoin = kucoin_client.create_market_order('BTC-USDT', 'sell', size=str(amount_to_trade))

                # حساب الربح (مبسط)
                profit = (kucoin_price - binance_price) * amount_to_trade

                trade = TradeLog(
                    user_id=user.id,
                    trade_type="arbitrage_buy_binance_sell_kucoin",
                    amount=amount_to_trade,
                    price=binance_price,
                    profit=profit
                )
                db.add(trade)
                db.commit()

                await bot.send_message(user.telegram_id, f"✅ تمت الصفقة وربحك المتوقع: {profit:.2f} USDT")

            elif kucoin_price + threshold < binance_price:
                # شراء من كوكوين وبيع في باينانس
                await bot.send_message(user.telegram_id, "🔄 فرصة مراجحة: شراء BTC من KuCoin وبيع في Binance")

                order_kucoin = kucoin_client.create_market_order('BTC-USDT', 'buy', size=str(amount_to_trade))
                order_binance = binance_client.order_market_sell(symbol="BTCUSDT", quantity=amount_to_trade)

                profit = (binance_price - kucoin_price) * amount_to_trade

                trade = TradeLog(
                    user_id=user.id,
                    trade_type="arbitrage_buy_kucoin_sell_binance",
                    amount=amount_to_trade,
                    price=kucoin_price,
                    profit=profit
                )
                db.add(trade)
                db.commit()

                await bot.send_message(user.telegram_id, f"✅ تمت الصفقة وربحك المتوقع: {profit:.2f} USDT")

            else:
                await bot.send_message(user.telegram_id, "⚠️ لا توجد فرص مراجحة حالياً.")

            # تحديث حالة المستخدم من قاعدة البيانات (في حالة التوقف)
            db.refresh(user)
            await asyncio.sleep(30)  # تأخير بين المحاولات

        except Exception as e:
            await bot.send_message(user.telegram_id, f"❌ خطأ في المراجحة: {str(e)}")
            await asyncio.sleep(60)  # انتظار أطول بعد الخطأ

    db.close()

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
