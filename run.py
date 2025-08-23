# run.py
import os
import logging
import asyncio
import decimal
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Set, Any, Union
from contextlib import contextmanager

import ccxt
from sqlalchemy import (
    create_engine, Column, Integer, String, Float,
    DateTime, Boolean, BigInteger, ForeignKey, text, inspect as sa_inspect
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.exceptions import ChatNotFound

# -----------------
# إعدادات البوت الأساسية
# -----------------
# قم بتعيين BOT_TOKEN في متغيرات البيئة قبل تشغيل البوت
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("يجب تعيين BOT_TOKEN كمتغير بيئة")

# إعدادات الـ Logging لتتبع الأخطاء
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# إعداد البوت
bot = Bot(token=BOT_TOKEN, parse_mode='HTML')
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# -----------------
# إعداد قاعدة البيانات
# -----------------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///arbitrage.db")
Base = declarative_base()

class User(Base):
    """جدول المستخدمين في قاعدة البيانات"""
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, index=True)
    base_investment = Column(Float, default=0.0)
    investment_status = Column(String(20), default="stopped")
    last_activity = Column(DateTime, default=datetime.utcnow)
    daily_profit = Column(Float, default=0.0)
    total_profit = Column(Float, default=0.0)
    trading_mode = Column(String(20), default="triangular")
    risk_level = Column(String(20), default="medium")
    exchanges = relationship("ExchangeCredential", back_populates="user", cascade="all, delete-orphan")

class ExchangeCredential(Base):
    """جدول بيانات المنصات للمستخدمين"""
    __tablename__ = "exchange_credentials"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    exchange_id = Column(String(50))
    api_key = Column(String(512))
    secret = Column(String(512))
    password = Column(String(512), nullable=True)
    user = relationship("User", back_populates="exchanges")

class Trade(Base):
    """جدول لتسجيل الصفقات الناجحة"""
    __tablename__ = "trades"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    pair = Column(String(100))
    side = Column(String(50))
    amount = Column(Float)
    price = Column(Float)
    fee = Column(Float)
    profit = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(String(500))
    status = Column(String(20), default="completed")
    rejection_reason = Column(String(200))
    trade_type = Column(String(20), default="triangular")
    user = relationship("User", backref="trades")

class RejectedTrade(Base):
    """جدول لتسجيل الصفقات المرفوضة أو الفاشلة"""
    __tablename__ = "rejected_trades"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    path = Column(String(300))
    expected_profit = Column(Float)
    rejection_reason = Column(String(200))
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(String(500))
    trade_type = Column(String(20), default="triangular")
    user = relationship("User", backref="rejected_trades")

class MarketData(Base):
    """جدول لتخزين بيانات السوق للحصول السريع على الحدود والعمولات"""
    __tablename__ = "market_data"
    id = Column(Integer, primary_key=True)
    symbol = Column(String(50), unique=True, index=True)
    min_amount = Column(Float, default=0.0)
    min_cost = Column(Float, default=0.0)
    price_precision = Column(Integer, default=8)
    amount_precision = Column(Integer, default=8)
    last_updated = Column(DateTime, default=datetime.utcnow)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(bind=engine)

@contextmanager
def db_session():
    """يوفر سياقًا للمعاملات لقاعدة البيانات"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def upgrade_database():
    """إنشاء الجداول في قاعدة البيانات إذا لم تكن موجودة"""
    try:
        inspector = sa_inspect(engine)
        if not inspector.has_table("users"):
            Base.metadata.create_all(engine)
            logger.info("تم إنشاء الجداول بنجاح.")
            return

        with engine.connect() as conn:
            cols = [c['name'] for c in inspector.get_columns('users')]
            if 'trading_mode' not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN trading_mode VARCHAR(20) DEFAULT 'triangular'"))
                logger.info("تم إضافة عمود 'trading_mode' إلى جدول 'users'.")
            if 'risk_level' not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN risk_level VARCHAR(20) DEFAULT 'medium'"))
                logger.info("تم إضافة عمود 'risk_level' إلى جدول 'users'.")
            if not inspector.has_table("market_data"):
                MarketData.__table__.create(engine)
                logger.info("تم إنشاء جدول 'market_data'.")
            conn.commit()
    except Exception as e:
        logger.error(f"خطأ أثناء تحديث قاعدة البيانات: {e}")

# -----------------
# منطق التداول
# -----------------
# ثوابت التداول
BNB_FEE_PERCENT = 0.001
MIN_PROFIT_PERCENT = 0.05
REQUEST_DELAY = 0.3
ARBITRAGE_CYCLE = 45 # ثواني

# المسارات المتاحة للتداول
TRIANGULAR_PATHS = [
    ("TRX/USDT", "TRX/BNB", "BNB/USDT"),
    ("WIN/USDT", "WIN/BNB", "BNB/USDT"),
    ("HOT/USDT", "HOT/BNB", "BNB/USDT"),
    ("SHIB/USDT", "SHIB/BNB", "BNB/USDT"),
    ("DOGE/USDT", "DOGE/BNB", "BNB/USDT"),
]
QUAD_PATHS = [
    ("TRX/USDT", "TRX/BNB", "BNB/BTC", "BTC/USDT"),
    ("XRP/USDT", "XRP/BNB", "BNB/ETH", "ETH/USDT"),
]
PENTA_PATHS = [
    ("TRX/USDT", "TRX/BNB", "BNB/BTC", "BTC/ETH", "ETH/USDT"),
]

class RetryManager:
    """إدارة إعادة المحاولة للطلبات الفاشلة"""
    def __init__(self, max_attempts=3, base_delay=1, max_delay=30):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay

    async def execute_with_retry(self, func, *args, **kwargs):
        last_exception = None
        for attempt in range(self.max_attempts):
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = await asyncio.to_thread(func, *args, **kwargs)
                return result
            except (ccxt.NetworkError, ccxt.ExchangeError, asyncio.TimeoutError) as e:
                last_exception = e
                delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                logger.warning(f"المحاولة {attempt + 1} فشلت، إعادة المحاولة بعد {delay} ثانية: {str(e)}")
                await asyncio.sleep(delay)
            except Exception as e:
                logger.error(f"خطأ غير متوقع: {str(e)}")
                raise e
        raise last_exception if last_exception else Exception("فشلت كل المحاولات")

class MarketCache:
    """تخزين مؤقت لبيانات السوق لتجنب الطلبات المتكررة"""
    def __init__(self, ttl_minutes=30):
        self.cache = {}
        self.ttl = timedelta(minutes=ttl_minutes)

    async def get_markets(self, exchange, force_reload=False):
        exchange_id = exchange.id
        now = datetime.now()
        if force_reload or exchange_id not in self.cache or now - self.cache[exchange_id]['timestamp'] > self.ttl:
            try:
                markets = await asyncio.to_thread(exchange.load_markets)
                self.cache[exchange_id] = {'markets': markets, 'timestamp': now}
                logger.info(f"تم تحميل {len(markets)} سوقًا لمنصة {exchange_id}")
                with db_session() as db:
                    for symbol, market in markets.items():
                        market_data = db.query(MarketData).filter_by(symbol=symbol).first() or MarketData(symbol=symbol)
                        limits = market.get('limits', {})
                        min_amount = limits.get('amount', {}).get('min')
                        min_cost = limits.get('cost', {}).get('min')
                        market_data.min_amount = float(min_amount) if min_amount is not None else 0.0
                        market_data.min_cost = float(min_cost) if min_cost is not None else 0.0
                        precision = market.get('precision', {})
                        market_data.price_precision = precision.get('price', 8)
                        market_data.amount_precision = precision.get('amount', 8)
                        market_data.last_updated = now
                        db.add(market_data)
            except Exception as e:
                if exchange_id in self.cache:
                    logger.warning(f"استخدام البيانات المخزنة مؤقتًا بسبب خطأ: {str(e)}")
                    return self.cache[exchange_id]['markets']
                raise e
        return self.cache[exchange_id]['markets']

retry_manager = RetryManager()
market_cache = MarketCache()

async def get_exchange(user_id: int) -> Optional[ccxt.Exchange]:
    """ينشئ كائن ccxt للمنصة المحددة"""
    with db_session() as db:
        user = db.query(User).filter_by(telegram_id=user_id).first()
        if not user or not user.exchanges:
            return None
        cred = user.exchanges[0]
        exchange_id = cred.exchange_id.lower()
        if not hasattr(ccxt, exchange_id):
            return None
        exchange_class = getattr(ccxt, exchange_id)
        exchange = exchange_class({
            'apiKey': cred.api_key,
            'secret': cred.secret,
            'password': cred.password,
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
        try:
            await market_cache.get_markets(exchange)
            return exchange
        except Exception as e:
            logger.error(f"فشل في تحميل الأسواق: {str(e)}")
            return None

async def check_balance(exchange, currency: str = 'USDT') -> float:
    """يتحقق من رصيد عملة معينة"""
    try:
        balance = await retry_manager.execute_with_retry(exchange.fetch_free_balance)
        return float(balance.get(currency, 0.0))
    except Exception as e:
        logger.error(f"خطأ في جلب الرصيد: {str(e)}")
        return 0.0

async def check_arbitrage_path(exchange, path: Tuple[str, ...], quote_amount: float) -> Optional[float]:
    """يحلل مسار المراجحة ويحسب الربح المحتمل"""
    try:
        current_prices = {}
        for symbol in path:
            ticker = await retry_manager.execute_with_retry(exchange.fetch_ticker, symbol)
            if not ticker or 'last' not in ticker or ticker['last'] is None:
                return None
            current_prices[symbol] = float(ticker['last'])

        amt = decimal.Decimal(str(quote_amount))
        for symbol in path:
            base, quote = symbol.split('/')
            fee = decimal.Decimal(str(exchange.markets[symbol]['taker']))
            price = decimal.Decimal(str(current_prices[symbol]))
            if '/USDT' in symbol: # assuming first leg is always from USDT
                amt = (amt / price) * (decimal.Decimal('1') - fee)
            else:
                amt = (amt * price) * (decimal.Decimal('1') - fee)

        final_amount = float(amt)
        net_profit = final_amount - quote_amount
        return net_profit if net_profit > 0 else None
    except Exception as e:
        logger.error(f"خطأ في تحليل المسار {path}: {str(e)}")
        return None

async def execute_arbitrage(user_id: int, path: Tuple[str, ...], quote_amount: float, bot_instance) -> bool:
    """ينفذ صفقة المراجحة على المنصة"""
    exchange = await get_exchange(user_id)
    if not exchange: return False
    
    current_amount = quote_amount
    trade_summary = []
    
    try:
        trade_summary.append(f"🔄 بدء صفقة مراجحة على المسار: {' → '.join(path)}")

        for i, symbol in enumerate(path):
            await asyncio.sleep(REQUEST_DELAY)
            base, quote = symbol.split('/')
            
            # Simplified execution logic (requires robust implementation)
            if i == 0:  # First leg: buy with USDT
                order_type = 'buy'
                price = float((await retry_manager.execute_with_retry(exchange.fetch_ticker, symbol))['ask'])
                amount_to_buy = current_amount / price
                order = await retry_manager.execute_with_retry(exchange.create_market_buy_order, symbol, amount_to_buy)
            else: # Other legs: sell to the next currency in the path
                order_type = 'sell'
                order = await retry_manager.execute_with_retry(exchange.create_market_sell_order, symbol, current_amount)

            if not order or order.get('status') != 'closed':
                raise Exception(f"فشلت الصفقة عند {symbol}")
            
            filled_amount = float(order.get('filled', 0))
            if filled_amount <= 0:
                raise Exception(f"لم يتم تنفيذ أي جزء من الصفقة عند {symbol}")

            current_amount = float(order.get('cost', 0))
            trade_summary.append(f"✅ تم تنفيذ: {order_type} {symbol}، الكمية: {filled_amount:.6f}")

        profit = current_amount - quote_amount
        trade_summary.append(f"🎉 تم بنجاح! الربح: {profit:.6f} USDT")
        
        with db_session() as db:
            user = db.query(User).filter_by(telegram_id=user_id).first()
            if user:
                user.total_profit += profit
                db.add(Trade(
                    user_id=user.id,
                    pair="->".join(path),
                    amount=quote_amount,
                    profit=profit,
                    details=" | ".join(trade_summary)
                ))
        
        await bot_instance.send_message(user_id, "\n".join(trade_summary))
        return True

    except Exception as e:
        await bot_instance.send_message(user_id, f"❌ خطأ أثناء تنفيذ الصفقة: {str(e)}")
        return False

# -----------------
# دورة التداول
# -----------------
async def enhanced_trading_cycle(user_id: int, bot_instance):
    """
    الدورة الرئيسية للتداول.
    تستمر في العمل حتى يقوم المستخدم بإيقافها.
    """
    try:
        with db_session() as db:
            user = db.query(User).filter_by(telegram_id=user_id).first()
            if not user or user.investment_status != "running":
                return
            
            exchange = await get_exchange(user_id)
            if not exchange:
                await bot_instance.send_message(user_id, "❌ فشل الاتصال بالمنصة.")
                return

            invest_amt = float(user.base_investment or 0.0)
            if invest_amt < 5.0:
                await bot_instance.send_message(user_id, "❌ يرجى تعيين مبلغ استثمار (الحد الأدنى 5 USDT).")
                return
            
            supported_paths = []
            if user.trading_mode == "triangular":
                supported_paths = TRIANGULAR_PATHS
            elif user.trading_mode == "quad":
                supported_paths = QUAD_PATHS
            elif user.trading_mode == "penta":
                supported_paths = PENTA_PATHS

            if not supported_paths:
                await bot_instance.send_message(user_id, "🔍 لا توجد مسارات تداول مدعومة لهذا الوضع.")
                return

            best_opportunity = None
            best_profit = -1

            for path in supported_paths:
                profit = await check_arbitrage_path(exchange, path, invest_amt)
                if profit is not None and profit > best_profit:
                    best_profit = profit
                    best_opportunity = path

            if best_opportunity:
                profit_percent = (best_profit / invest_amt) * 100
                await bot_instance.send_message(
                    user_id,
                    f"📈 فرصة مربحة! المسار: {' → '.join(best_opportunity)}\n"
                    f"الربح المحتمل: {best_profit:.6f} USDT ({profit_percent:.2f}%)"
                )
                success = await execute_arbitrage(user_id, best_opportunity, invest_amt, bot_instance)
                if not success:
                    logger.error(f"فشل تنفيذ صفقة المراجحة للمسار: {best_opportunity}")
            else:
                await bot_instance.send_message(user_id, "🔍 لا توجد فرص مربحة حالياً.")

    except ChatNotFound:
        # إذا تم حظر البوت بواسطة المستخدم
        logger.warning(f"تم حظر البوت بواسطة المستخدم {user_id}. إيقاف الدورة.")
        with db_session() as db:
            user = db.query(User).filter_by(telegram_id=user_id).first()
            if user:
                user.investment_status = "stopped"
    except Exception as e:
        logger.error(f"خطأ في دورة التداول: {str(e)}")
        # تجنب إرسال رسائل إذا كان الخطأ متكرراً
    finally:
        await asyncio.sleep(ARBITRAGE_CYCLE)
        with db_session() as db:
            user = db.query(User).filter_by(telegram_id=user_id).first()
            if user and user.investment_status == "running":
                asyncio.create_task(enhanced_trading_cycle(user_id, bot_instance))

# -----------------
# مقبضات (Handlers) البوت
# -----------------
class ExchangeStates(StatesGroup):
    choosing_exchange = State()
    entering_api_key = State()
    entering_secret = State()
    entering_password = State()

class InvestmentStates(StatesGroup):
    entering_amount = State()

def main_menu_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🔐 إدارة المنصات", callback_data="menu_exchanges"),
        types.InlineKeyboardButton("💰 تعيين المبلغ", callback_data="menu_investment")
    )
    kb.add(
        types.InlineKeyboardButton("⚙️ الإعدادات", callback_data="menu_settings"),
        types.InlineKeyboardButton("📊 كشف الحساب", callback_data="menu_report")
    )
    kb.add(
        types.InlineKeyboardButton("🚀 بدء التداول", callback_data="menu_start_trading"),
        types.InlineKeyboardButton("🛑 إيقاف البوت", callback_data="menu_stop_bot")
    )
    return kb

def back_keyboard():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🔙 العودة", callback_data="back_main"))
    return kb

def settings_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🔺 مثلثي", callback_data="setting_mode_triangular"),
        types.InlineKeyboardButton("🔷 رباعي", callback_data="setting_mode_quad"),
        types.InlineKeyboardButton("🔶 خماسي", callback_data="setting_mode_penta")
    )
    kb.add(
        types.InlineKeyboardButton("🟢 منخفض", callback_data="setting_risk_low"),
        types.InlineKeyboardButton("🟡 متوسط", callback_data="setting_risk_medium"),
        types.InlineKeyboardButton("🔴 عالي", callback_data="setting_risk_high")
    )
    kb.add(types.InlineKeyboardButton("🔙 العودة", callback_data="back_main"))
    return kb

# --- المقبضات الفعلية ---
@dp.message_handler(commands=["start", "help"])
async def cmd_start(message: types.Message):
    with db_session() as db:
        user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
        if not user:
            user = User(telegram_id=message.from_user.id)
            db.add(user)
    await message.answer(
        "🤖 <b>مرحباً بك في بوت المراجحة الذكية</b>\n\n"
        "• إدارة تلقائية لرصيد BNB\n"
        "• إعادة استثمار الأرباح تلقائياً\n\n"
        "🚀 ابدأ بإضافة منصة Binance ثم تعيين مبلغ الاستثمار",
        reply_markup=main_menu_keyboard()
    )

@dp.callback_query_handler(lambda c: c.data == "back_main")
async def back_main(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await callback_query.answer()
    await callback_query.message.edit_text("🏠 القائمة الرئيسية", reply_markup=main_menu_keyboard())

@dp.callback_query_handler(lambda c: c.data == "menu_exchanges")
async def menu_exchanges(callback_query: types.CallbackQuery):
    await callback_query.answer()
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Binance", callback_data="exchange_binance"))
    kb.add(types.InlineKeyboardButton("🔙 العودة", callback_data="back_main"))
    await callback_query.message.edit_text("💹 اختر المنصة:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("exchange_"), state=None)
async def select_exchange(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    exchange_name = callback_query.data.split("_")[1].capitalize()
    await state.update_data(exchange_name=exchange_name)
    await ExchangeStates.entering_api_key.set()
    await callback_query.message.edit_text(f"🔑 أدخل API Key لـ {exchange_name}:", reply_markup=back_keyboard())

@dp.message_handler(state=ExchangeStates.entering_api_key)
async def enter_api_key(message: types.Message, state: FSMContext):
    await state.update_data(api_key=message.text.strip())
    await ExchangeStates.next()
    await message.answer("🔒 أدخل Secret Key:", reply_markup=back_keyboard())

@dp.message_handler(state=ExchangeStates.entering_secret)
async def enter_secret(message: types.Message, state: FSMContext):
    await state.update_data(secret=message.text.strip())
    await ExchangeStates.next()
    await message.answer("🔑 أدخل Password (أو 'لا' إذا لم يكن موجوداً):", reply_markup=back_keyboard())

@dp.message_handler(state=ExchangeStates.entering_password)
async def enter_password(message: types.Message, state: FSMContext):
    data = await state.get_data()
    password = message.text.strip() if message.text.strip().lower() != "لا" else None
    with db_session() as db:
        user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
        if user:
            db.query(ExchangeCredential).filter_by(user_id=user.id, exchange_id=data['exchange_name']).delete()
            exchange = ExchangeCredential(user_id=user.id, exchange_id=data['exchange_name'], api_key=data['api_key'], secret=data['secret'], password=password)
            db.add(exchange)
    await state.finish()
    await message.answer("✅ تم حفظ بيانات المنصة بنجاح!", reply_markup=main_menu_keyboard())

@dp.callback_query_handler(lambda c: c.data == "menu_investment", state=None)
async def menu_investment(callback_query: types.CallbackQuery):
    await callback_query.answer()
    await InvestmentStates.entering_amount.set()
    await callback_query.message.edit_text("💵 أدخل مبلغ الاستثمار (الحد الأدنى 5 USDT):", reply_markup=back_keyboard())

@dp.message_handler(state=InvestmentStates.entering_amount)
async def enter_investment_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text)
        if amount < 5.0:
            await message.answer("❌ المبلغ يجب ألا يقل عن 5 USDT. حاول مرة أخرى:")
            return
        with db_session() as db:
            user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
            if user:
                user.base_investment = amount
        await state.finish()
        await message.answer(f"✅ تم تعيين مبلغ الاستثمار إلى {amount:.2f} USDT", reply_markup=main_menu_keyboard())
    except ValueError:
        await message.answer("❌ صيغة المبلغ غير صحيحة. يرجى إدخال رقم:")

@dp.callback_query_handler(lambda c: c.data == "menu_settings")
async def menu_settings(callback_query: types.CallbackQuery):
    await callback_query.answer()
    await callback_query.message.edit_text("⚙️ إعدادات التداول:", reply_markup=settings_keyboard())

@dp.callback_query_handler(lambda c: c.data.startswith("setting_"))
async def handle_settings(callback_query: types.CallbackQuery):
    await callback_query.answer()
    setting_type, setting_value = callback_query.data.split("_")[1:]
    with db_session() as db:
        user = db.query(User).filter_by(telegram_id=callback_query.from_user.id).first()
        if user:
            if setting_type == "mode":
                user.trading_mode = setting_value
            elif setting_type == "risk":
                user.risk_level = setting_value
            await callback_query.message.edit_text(
                f"✅ تم تحديث الإعداد: {setting_type} = {setting_value}",
                reply_markup=main_menu_keyboard()
            )

@dp.callback_query_handler(lambda c: c.data == "menu_start_trading")
async def menu_start_trading(callback_query: types.CallbackQuery):
    await callback_query.answer()
    with db_session() as db:
        user = db.query(User).filter_by(telegram_id=callback_query.from_user.id).first()
        if user:
            user.investment_status = "running"
            await callback_query.message.edit_text("🚀 بدء التداول...", reply_markup=main_menu_keyboard())
            asyncio.create_task(enhanced_trading_cycle(user.telegram_id, callback_query.bot))

@dp.callback_query_handler(lambda c: c.data == "menu_stop_bot")
async def menu_stop_bot(callback_query: types.CallbackQuery):
    await callback_query.answer()
    with db_session() as db:
        user = db.query(User).filter_by(telegram_id=callback_query.from_user.id).first()
        if user:
            user.investment_status = "stopped"
    await callback_query.message.edit_text("🛑 تم إيقاف البوت. لن يتم تنفيذ أي عمليات جديدة.", reply_markup=main_menu_keyboard())

@dp.callback_query_handler(lambda c: c.data == "menu_report")
async def menu_report(callback_query: types.CallbackQuery):
    await callback_query.answer()
    with db_session() as db:
        user = db.query(User).filter_by(telegram_id=callback_query.from_user.id).first()
        report = f"📊 <b>كشف الحساب</b>\n"
        report += f"• إجمالي الربح: {user.total_profit:.6f} USDT\n"
        report += f"• ربح اليوم: {user.daily_profit:.6f} USDT\n"
        report += f"• آخر استثمار: {user.base_investment:.2f} USDT\n"
    await callback_query.message.edit_text(report, reply_markup=main_menu_keyboard())

# -----------------
# وظيفة التشغيل
# -----------------
async def on_startup(dp):
    logger.info("Starting bot...")
    upgrade_database()
    logger.info("Database tables checked/upgraded successfully.")

async def on_shutdown(dp):
    logger.info("Shutting down bot...")
    await dp.storage.close()
    await dp.storage.wait_closed()
    await dp.bot.close()

if __name__ == '__main__':
    from aiogram import executor
    logger.info("Starting bot polling...")
    executor.start_polling(dp, on_startup=on_startup, on_shutdown=on_shutdown)