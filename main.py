# main.py
import os
import asyncio
import logging
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from sqlalchemy import (
    create_engine, Column, BigInteger, Integer, String, Float, DateTime, Boolean, text
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Exchange SDKs
from binance.client import Client as BinanceClient
from kucoin.client import Market as KuCoinMarket, Trade as KuCoinTrade

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --------- Config from env ----------
BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
RESET_DB = os.getenv("RESET_DB", "0")  # set to "1" to drop & recreate tables (you said you'll recreate DB)

if not BOT_TOKEN or not DATABASE_URL:
    raise Exception("Missing BOT_TOKEN or DATABASE_URL environment variables.")

# ensure SQLAlchemy URL uses pymysql driver if MySQL short form provided
if DATABASE_URL.startswith("mysql://"):
    DATABASE_URL = DATABASE_URL.replace("mysql://", "mysql+pymysql://")

# --------- Bot & DB setup ----------
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

Base = declarative_base()
engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# --------- Models ----------
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    # API keys
    binance_api = Column(String(256), nullable=True)
    binance_secret = Column(String(256), nullable=True)
    binance_active = Column(Boolean, nullable=False, server_default=text("0"))
    kucoin_api = Column(String(256), nullable=True)
    kucoin_secret = Column(String(256), nullable=True)
    kucoin_passphrase = Column(String(256), nullable=True)
    kucoin_active = Column(Boolean, nullable=False, server_default=text("0"))
    # investment
    investment_amount = Column(Float, default=0.0, nullable=False)
    investment_status = Column(String(20), default="stopped", nullable=False)  # started/stopped

class TradeLog(Base):
    __tablename__ = "trade_logs"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    trade_type = Column(String(50))
    amount = Column(Float)
    price = Column(Float)
    profit = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

# create or reset DB if requested
if RESET_DB == "1":
    logger.info("RESET_DB=1 -> dropping all tables and recreating.")
    Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

# --------- FSM States ----------
class Form(StatesGroup):
    selected_platform = State()
    waiting_api_key = State()
    waiting_secret_key = State()
    waiting_passphrase = State()
    waiting_investment_amount = State()
    waiting_report_start = State()
    waiting_report_end = State()

# --------- Helpers ----------
def create_binance_client(user: User):
    if user and user.binance_api and user.binance_secret:
        return BinanceClient(user.binance_api, user.binance_secret)
    return None

def create_kucoin_clients(user: User):
    if user and user.kucoin_api and user.kucoin_secret and user.kucoin_passphrase:
        market = KuCoinMarket()
        trade = KuCoinTrade(user.kucoin_api, user.kucoin_secret, user.kucoin_passphrase)
        return market, trade
    return None, None

# NOTE: These verifications call blocking SDKs. For production you might run them in executor.
async def verify_binance_keys(api_key: str, secret_key: str) -> (bool, str):
    try:
        client = BinanceClient(api_key, secret_key)
        client.get_account()  # will raise on invalid
        return True, ""
    except Exception as e:
        return False, str(e)

async def verify_kucoin_keys(api_key: str, secret_key: str, passphrase: str) -> (bool, str):
    try:
        trade = KuCoinTrade(api_key, secret_key, passphrase)
        trade.get_account()
        return True, ""
    except Exception as e:
        return False, str(e)

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

def user_platforms_keyboard(user: User):
    kb = InlineKeyboardMarkup(row_width=1)
    # Binance
    binance_label = "Binance"
    if user.binance_api:
        binance_label = ("✅ Binance" if user.binance_active else "❌ Binance") + " (مربوط)"
    else:
        binance_label = "Binance (غير مربوط)"
    # KuCoin
    kucoin_label = "KuCoin"
    if user.kucoin_api:
        kucoin_label = ("✅ KuCoin" if user.kucoin_active else "❌ KuCoin") + " (مربوط)"
    else:
        kucoin_label = "KuCoin (غير مربوط)"

    kb.add(InlineKeyboardButton(binance_label, callback_data="platform_binance"))
    kb.add(InlineKeyboardButton(kucoin_label, callback_data="platform_kucoin"))
    kb.add(InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu"))
    return kb

# --------- Handlers ---------
@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
        if not user:
            user = User(telegram_id=message.from_user.id)
            db.add(user)
            db.commit()
        await message.answer("أهلاً بك — اختر من القائمة:", reply_markup=main_menu_keyboard())
    except Exception as e:
        logger.exception("start handler error")
        await message.answer("حدث خطأ داخلي.")
    finally:
        db.close()

@dp.callback_query_handler(lambda c: c.data == "main_menu")
async def cb_main_menu(call: types.CallbackQuery):
    await call.answer()
    await call.message.edit_text("القائمة الرئيسية:", reply_markup=main_menu_keyboard())

# --- edit trading data menu ---
@dp.callback_query_handler(lambda c: c.data == "menu_edit_trading_data")
async def cb_edit_trading(call: types.CallbackQuery):
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=call.from_user.id).first()
        if not user:
            await call.answer("لم يتم العثور على حسابك. أرسل /start.")
            return
        await call.message.edit_text("اختر منصة لإضافة/تعديل المفاتيح:", reply_markup=user_platforms_keyboard(user))
        await call.answer()
    finally:
        db.close()

@dp.callback_query_handler(lambda c: c.data.startswith("platform_"))
async def cb_platform(call: types.CallbackQuery, state: FSMContext):
    platform = call.data.split("_", 1)[1]  # 'binance' or 'kucoin'
    await state.update_data(selected_platform=platform)
    await call.answer()
    await call.message.edit_text(f"أرسل مفتاح API لمنصة {platform.capitalize()}:")
    await Form.waiting_api_key.set()

@dp.message_handler(state=Form.waiting_api_key)
async def handle_api_key(message: types.Message, state: FSMContext):
    api_key = message.text.strip()
    await state.update_data(api_key=api_key)
    data = await state.get_data()
    platform = data.get("selected_platform")
    if platform == "binance":
        await message.answer("أرسل Secret Key الخاص بباينانس:")
        await Form.waiting_secret_key.set()
    elif platform == "kucoin":
        await message.answer("أرسل Secret Key الخاص بكوكوين:")
        await Form.waiting_secret_key.set()
    else:
        await message.answer("خيار غير معروف.")
        await state.finish()

@dp.message_handler(state=Form.waiting_secret_key)
async def handle_secret_key(message: types.Message, state: FSMContext):
    secret_key = message.text.strip()
    data = await state.get_data()
    api_key = data.get("api_key")
    platform = data.get("selected_platform")

    await state.update_data(secret_key=secret_key)

    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
        if platform == "binance":
            valid, err = await verify_binance_keys(api_key, secret_key)
            if not valid:
                await message.answer(f"❌ فشل التحقق من مفاتيح Binance: {err}\nأرسل /menu_edit_trading_data وحاول مرة أخرى.")
                await state.finish()
                return
            user.binance_api = api_key
            user.binance_secret = secret_key
            user.binance_active = True
            db.add(user)
            db.commit()
            await message.answer("✅ تم ربط وتفعيل Binance بنجاح.")
            await message.answer("العودة للقائمة الرئيسية:", reply_markup=main_menu_keyboard())
            await state.finish()
            return

        elif platform == "kucoin":
            # ask for passphrase next
            await message.answer("أرسل passphrase الخاص بـ KuCoin:")
            await Form.waiting_passphrase.set()
            return
    except Exception as e:
        logger.exception("handle_secret_key error")
        await message.answer("حدث خطأ أثناء حفظ المفاتيح.")
    finally:
        db.close()

@dp.message_handler(state=Form.waiting_passphrase)
async def handle_passphrase(message: types.Message, state: FSMContext):
    passphrase = message.text.strip()
    data = await state.get_data()
    api_key = data.get("api_key")
    secret_key = data.get("secret_key") or data.get("secret") or data.get("secret_key")  # try multiple keys
    platform = data.get("selected_platform")

    # note: earlier we stored secret under 'secret_key' in this handler
    # ensure correct variable:
    secret_key = data.get("secret_key", secret_key)

    valid, err = await verify_kucoin_keys(api_key, secret_key, passphrase)
    if not valid:
        await message.answer(f"❌ فشل التحقق من مفاتيح KuCoin: {err}\nأرسل /menu_edit_trading_data وحاول مرة أخرى.")
        await state.finish()
        return

    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
        user.kucoin_api = api_key
        user.kucoin_secret = secret_key
        user.kucoin_passphrase = passphrase
        user.kucoin_active = True
        db.add(user)
        db.commit()
        await message.answer("✅ تم ربط وتفعيل KuCoin بنجاح.")
        await message.answer("العودة للقائمة الرئيسية:", reply_markup=main_menu_keyboard())
    except Exception:
        logger.exception("handle_passphrase error")
        await message.answer("حدث خطأ أثناء حفظ مفاتيح KuCoin.")
    finally:
        db.close()
        await state.finish()

# --- Start invest ---
@dp.callback_query_handler(lambda c: c.data == "menu_start_invest")
async def cb_start_invest(call: types.CallbackQuery):
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=call.from_user.id).first()
        if not user or (not user.binance_active and not user.kucoin_active):
            await call.answer("❌ لم تقم بربط أي منصة مفعلة.")
            return
        if user.investment_amount <= 0:
            await call.answer("❌ لم تحدد مبلغ الاستثمار. اذهب إلى القائمة وحدد المبلغ.")
            return
        user.investment_status = "started"
        db.add(user)
        db.commit()
        await call.answer()
        await call.message.edit_text("🚀 تم بدء المراجحة التلقائية. سترسل لك تحديثات عند تنفيذ صفقات.")
        asyncio.create_task(run_arbitrage_loop(call.from_user.id))
    finally:
        db.close()

# --- Fake invest (placeholder) ---
@dp.callback_query_handler(lambda c: c.data == "menu_fake_invest")
async def cb_fake_invest(call: types.CallbackQuery):
    await call.answer()
    await call.message.edit_text("🛑 وضع المحاكاة (Demo) مفعّل - يعرض ماذا كان سيحصل بدون تنفيذ صفقات حقيقية.\n(الميزة تحت التطوير)")

# --- Report handlers ---
@dp.callback_query_handler(lambda c: c.data == "menu_report")
async def cb_report_start(call: types.CallbackQuery):
    await call.answer()
    await call.message.edit_text("📅 أرسل تاريخ بداية الفترة بصيغة YYYY-MM-DD")
    await Form.waiting_report_start.set()

@dp.message_handler(state=Form.waiting_report_start)
async def handle_report_start(message: types.Message, state: FSMContext):
    try:
        start = datetime.strptime(message.text.strip(), "%Y-%m-%d")
        await state.update_data(report_start=start)
        await message.answer("📅 الآن أرسل تاريخ نهاية الفترة بصيغة YYYY-MM-DD")
        await Form.waiting_report_end.set()
    except Exception:
        await message.answer("تنسيق غير صحيح. استخدم YYYY-MM-DD")

@dp.message_handler(state=Form.waiting_report_end)
async def handle_report_end(message: types.Message, state: FSMContext):
    try:
        end = datetime.strptime(message.text.strip(), "%Y-%m-%d")
        data = await state.get_data()
        start = data.get("report_start")
        if not start:
            await message.answer("لم يتم إدخال تاريخ البداية. ابدأ من جديد.")
            await state.finish()
            return
        if end < start:
            await message.answer("تاريخ النهاية أصغر من البداية.")
            return

        db = SessionLocal()
        try:
            user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
            trades = db.query(TradeLog).filter(
                TradeLog.user_id == user.id,
                TradeLog.timestamp >= start,
                TradeLog.timestamp <= end + timedelta(days=1)
            ).all()
        finally:
            db.close()

        if not trades:
            await message.answer("لا توجد صفقات في هذه الفترة.")
            await state.finish()
            return

        text = f"📊 كشف حساب من {start.date()} إلى {end.date()}:\n"
        total = 0.0
        for t in trades:
            text += f"- {t.timestamp.date()}: {t.trade_type} ربح {t.profit:.2f} USDT\n"
            total += (t.profit or 0.0)
        text += f"\n💰 إجمالي الربح: {total:.2f} USDT"
        await message.answer(text)
        await state.finish()
    except Exception:
        await message.answer("تنسيق غير صحيح أو خطأ. استخدم YYYY-MM-DD")
        await state.finish()

# --- Market status ---
@dp.callback_query_handler(lambda c: c.data == "menu_market_status")
async def cb_market_status(call: types.CallbackQuery):
    await call.answer()
    # placeholder simple analysis
    await call.message.edit_text("📈 حالة السوق (تحليل مبسط):\n- تقلبات متوسطة.\n- نصيحة: راجع محفظتك قبل البدء.", reply_markup=main_menu_keyboard())

# --- Stop invest ---
@dp.callback_query_handler(lambda c: c.data == "menu_stop_invest")
async def cb_stop_invest(call: types.CallbackQuery):
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=call.from_user.id).first()
        if not user:
            await call.answer("❌ لم يتم العثور على حسابك.")
            return
        user.investment_status = "stopped"
        db.add(user)
        db.commit()
        await call.answer()
        await call.message.edit_text("⏹️ تم إيقاف الاستثمار.", reply_markup=main_menu_keyboard())
    finally:
        db.close()

# ---------------- Arbitrage loop ----------------
async def run_arbitrage_loop(telegram_id: int):
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=telegram_id).first()
        if not user or user.investment_status != "started":
            return

        while True:
            db.refresh(user)
            if user.investment_status != "started":
                return

            try:
                binance_client = create_binance_client(user)
                kucoin_market, kucoin_trade = create_kucoin_clients(user)

                if not binance_client and not kucoin_trade:
                    await bot.send_message(user.telegram_id, "❌ لا توجد منصات مفعلة.")
                    user.investment_status = "stopped"
                    db.add(user)
                    db.commit()
                    return

                # get prices (example BTC-USDT)
                b_price = None
                k_price = None
                if binance_client:
                    b_price = float(binance_client.get_symbol_ticker(symbol="BTCUSDT")['price'])
                if kucoin_market:
                    k_price = float(kucoin_market.get_ticker("BTC-USDT")['price'])

                threshold = 20.0
                amount = 0.0
                if user.investment_amount > 0:
                    prices = [p for p in (b_price, k_price) if p is not None]
                    min_p = min(prices) if prices else None
                    if min_p:
                        amount = user.investment_amount / min_p

                trade_type = None
                profit = 0.0

                if b_price and k_price:
                    if b_price + threshold < k_price and binance_client and kucoin_trade:
                        # buy on binance, sell on kucoin
                        try:
                            binance_client.order_market_buy(symbol="BTCUSDT", quantity=amount)
                            kucoin_trade.create_market_order('BTC-USDT', 'sell', size=str(amount))
                            profit = (k_price - b_price) * amount
                            trade_type = "Buy Binance / Sell KuCoin"
                        except Exception as e:
                            logger.exception("trade error")
                    elif k_price + threshold < b_price and kucoin_trade and binance_client:
                        try:
                            kucoin_trade.create_market_order('BTC-USDT', 'buy', size=str(amount))
                            binance_client.order_market_sell(symbol="BTCUSDT", quantity=amount)
                            profit = (b_price - k_price) * amount
                            trade_type = "Buy KuCoin / Sell Binance"
                        except Exception as e:
                            logger.exception("trade error")

                if trade_type:
                    t = TradeLog(
                        user_id=user.id,
                        trade_type=trade_type,
                        amount=amount,
                        price=min(b_price, k_price) if (b_price and k_price) else (b_price or k_price or 0),
                        profit=profit,
                    )
                    db.add(t)
                    db.commit()
                    await bot.send_message(user.telegram_id,
                        f"✅ تمت مراجحة: {trade_type}\nكمية BTC: {amount:.6f}\nربح تقديري: {profit:.2f} USDT")
                else:
                    await bot.send_message(user.telegram_id, "⚠️ لا توجد فرص مراجحة الآن.")

                await asyncio.sleep(30)
            except Exception as e:
                logger.exception("run_arbitrage_loop error")
                await bot.send_message(user.telegram_id, f"❌ خطأ أثناء المراجحة: {str(e)}")
                await asyncio.sleep(60)
    finally:
        db.close()

# -------- Run bot ----------
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
