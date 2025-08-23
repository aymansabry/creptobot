# run.py
import os
import logging
import asyncio
import decimal
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Set, Any, Union
from contextlib import contextmanager

# -----------------
# Importing essential libraries
# -----------------
import ccxt
from sqlalchemy import (
    create_engine, Column, Integer, String, Float,
    DateTime, Boolean, BigInteger, ForeignKey, text, inspect as sa_inspect
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramAPIError
from aiogram.client.default import DefaultBotProperties
from aiogram import Router
from aiogram import F
from aiogram.filters import CommandStart, Command, StateFilter

# -----------------
# Core Bot & Logging Setup
# -----------------
# Set BOT_TOKEN as an environment variable
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN must be set as an environment variable.")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# -----------------
# Database Models & Setup
# -----------------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///arbitrage.db")
Base = declarative_base()

class User(Base):
    """Database table for users."""
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
    """Database table for user's exchange credentials."""
    __tablename__ = "exchange_credentials"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    exchange_id = Column(String(50))
    api_key = Column(String(512))
    secret = Column(String(512))
    password = Column(String(512), nullable=True)
    user = relationship("User", back_populates="exchanges")

class Trade(Base):
    """Database table for successful trades."""
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
    """Database table for rejected or failed trades."""
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
    """Table for storing market data to reduce API calls."""
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
    """Provides a transactional scope around a series of operations."""
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
    """Checks for database tables and creates them if they don't exist."""
    try:
        inspector = sa_inspect(engine)
        if not inspector.has_table("users"):
            Base.metadata.create_all(engine)
            logger.info("Tables created successfully.")
            return
        with engine.connect() as conn:
            cols = [c['name'] for c in inspector.get_columns('users')]
            if 'trading_mode' not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN trading_mode VARCHAR(20) DEFAULT 'triangular'"))
                logger.info("Added 'trading_mode' column to 'users' table.")
            if 'risk_level' not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN risk_level VARCHAR(20) DEFAULT 'medium'"))
                logger.info("Added 'risk_level' column to 'users' table.")
            if not inspector.has_table("market_data"):
                MarketData.__table__.create(engine)
                logger.info("Created 'market_data' table.")
            conn.commit()
    except Exception as e:
        logger.error(f"Error during database upgrade: {e}")

# -----------------
# Trading Logic & Utilities
# -----------------
# Trading constants
MIN_PROFIT_PERCENT = 0.05
REQUEST_DELAY = 0.3
ARBITRAGE_CYCLE = 45 # Seconds

# Supported arbitrage paths
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
    """Manages retries for failed API requests."""
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
                logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay} seconds: {str(e)}")
                await asyncio.sleep(delay)
            except Exception as e:
                logger.error(f"Unexpected error in execute_with_retry: {str(e)}")
                raise e
        raise last_exception if last_exception else Exception("Failed after all attempts")

class MarketCache:
    """Caches market data to reduce API calls."""
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
                logger.info(f"Loaded {len(markets)} markets for {exchange_id}")
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
                    logger.warning(f"Using cached market data due to error: {str(e)}")
                    return self.cache[exchange_id]['markets']
                raise e
        return self.cache[exchange_id]['markets']

retry_manager = RetryManager()
market_cache = MarketCache()

async def get_exchange(user_id: int) -> Optional[ccxt.Exchange]:
    """Creates a ccxt object for the specified exchange."""
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
            logger.error(f"Failed to load markets: {str(e)}")
            return None

async def check_balance(exchange, currency: str = 'USDT') -> float:
    """Checks the balance of a specific currency."""
    try:
        balance = await retry_manager.execute_with_retry(exchange.fetch_free_balance)
        return float(balance.get(currency, 0.0))
    except Exception as e:
        logger.error(f"Error fetching balance: {str(e)}")
        return 0.0

async def check_arbitrage_path(exchange, path: Tuple[str, ...], quote_amount: float) -> Optional[float]:
    """Analyzes an arbitrage path and calculates the potential profit."""
    try:
        current_prices = {}
        for symbol in path:
            ticker = await retry_manager.execute_with_retry(exchange.fetch_ticker, symbol)
            if not ticker or 'last' not in ticker or ticker['last'] is None:
                return None
            current_prices[symbol] = float(ticker['last'])

        amt = decimal.Decimal(str(quote_amount))
        for symbol in path:
            # Simplified logic for demonstration
            price = decimal.Decimal(str(current_prices[symbol]))
            if '/USDT' in symbol:
                amt = (amt / price) * (decimal.Decimal('1') - decimal.Decimal(str(exchange.markets[symbol]['taker'])))
            else:
                amt = (amt * price) * (decimal.Decimal('1') - decimal.Decimal(str(exchange.markets[symbol]['taker'])))

        final_amount = float(amt)
        net_profit = final_amount - quote_amount
        return net_profit if net_profit > 0 else None
    except Exception as e:
        logger.error(f"Error analyzing path {path}: {str(e)}")
        return None

async def execute_arbitrage(user_id: int, path: Tuple[str, ...], quote_amount: float, bot_instance) -> bool:
    """Executes the arbitrage trade on the exchange."""
    exchange = await get_exchange(user_id)
    if not exchange: return False
    
    current_amount = quote_amount
    trade_summary = []
    
    try:
        trade_summary.append(f"🔄 Starting arbitrage trade on path: {' → '.join(path)}")

        for i, symbol in enumerate(path):
            await asyncio.sleep(REQUEST_DELAY)
            
            # This is a simplified example. Real-world logic needs to be more robust.
            if i == 0:
                price = float((await retry_manager.execute_with_retry(exchange.fetch_ticker, symbol))['ask'])
                amount_to_buy = current_amount / price
                order = await retry_manager.execute_with_retry(exchange.create_market_buy_order, symbol, amount_to_buy)
            else:
                order = await retry_manager.execute_with_retry(exchange.create_market_sell_order, symbol, current_amount)

            if not order or order.get('status') != 'closed':
                raise Exception(f"Trade failed at {symbol}")
            
            filled_amount = float(order.get('filled', 0))
            if filled_amount <= 0:
                raise Exception(f"Order filled 0 at {symbol}")

            current_amount = float(order.get('cost', 0))
            trade_summary.append(f"✅ Executed: {'sell' if i > 0 else 'buy'} {symbol} with amount {filled_amount:.6f}")

        profit = current_amount - quote_amount
        trade_summary.append(f"🎉 Success! Profit: {profit:.6f} USDT")
        
        with db_session() as db:
            user = db.query(User).filter_by(telegram_id=user_id).first()
            if user:
                user.total_profit += profit
                db.add(Trade(user_id=user.id, pair="->".join(path), amount=quote_amount, profit=profit, details=" | ".join(trade_summary)))
        
        await bot_instance.send_message(user_id, "\n".join(trade_summary))
        return True

    except Exception as e:
        await bot_instance.send_message(user_id, f"❌ An error occurred during trade execution: {str(e)}")
        return False

# -----------------
# Main Trading Loop
# -----------------
async def enhanced_trading_cycle(user_id: int, bot_instance):
    """The main trading loop that runs continuously."""
    try:
        while True: # Loop indefinitely until user stops it
            with db_session() as db:
                user = db.query(User).filter_by(telegram_id=user_id).first()
                if not user or user.investment_status != "running":
                    logger.info(f"Stopping trading cycle for user {user_id}.")
                    break # Exit the loop
                
                exchange = await get_exchange(user.telegram_id)
                if not exchange:
                    await bot_instance.send_message(user.telegram_id, "❌ Failed to connect to the exchange. Stopping trading.")
                    user.investment_status = "stopped"
                    break
                
                invest_amt = float(user.base_investment or 0.0)
                if invest_amt < 5.0:
                    await bot_instance.send_message(user.telegram_id, "❌ Please set an investment amount (min 5 USDT). Stopping trading.")
                    user.investment_status = "stopped"
                    break
                
                supported_paths = []
                if user.trading_mode == "triangular":
                    supported_paths = TRIANGULAR_PATHS
                elif user.trading_mode == "quad":
                    supported_paths = QUAD_PATHS
                elif user.trading_mode == "penta":
                    supported_paths = PENTA_PATHS

                if not supported_paths:
                    await bot_instance.send_message(user.telegram_id, "🔍 No supported paths found for this trading mode. Stopping trading.")
                    user.investment_status = "stopped"
                    break

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
                        user.telegram_id,
                        f"📈 Profitable opportunity found: {' → '.join(best_opportunity)}\n"
                        f"Expected Profit: {best_profit:.6f} USDT ({profit_percent:.2f}%)"
                    )
                    await execute_arbitrage(user.telegram_id, best_opportunity, invest_amt, bot_instance)
                else:
                    await bot_instance.send_message(user.telegram_id, "🔍 No profitable opportunities found at the moment.")

            await asyncio.sleep(ARBITRAGE_CYCLE)

    except TelegramAPIError:
        logger.warning(f"Bot was blocked by user {user_id}. Stopping cycle.")
        with db_session() as db:
            user = db.query(User).filter_by(telegram_id=user_id).first()
            if user: user.investment_status = "stopped"
    except Exception as e:
        logger.error(f"An error occurred in the trading cycle: {str(e)}")
        await bot_instance.send_message(user_id, f"❌ A critical error occurred in the trading cycle: {str(e)}. Stopping bot.")
        with db_session() as db:
            user = db.query(User).filter_by(telegram_id=user_id).first()
            if user: user.investment_status = "stopped"
    finally:
        # Final cleanup or notification
        logger.info(f"Trading cycle for user {user_id} has concluded.")

# -----------------
# Bot Handlers & FSM
# -----------------
router = Router()

class ExchangeStates(StatesGroup):
    choosing_exchange = State()
    entering_api_key = State()
    entering_secret = State()
    entering_password = State()

class InvestmentStates(StatesGroup):
    entering_amount = State()

# --- Keyboards ---
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

# --- Actual Handlers ---
@router.message(CommandStart())
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

@router.callback_query(F.data == "back_main")
async def back_main(callback_query: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback_query.answer()
    await callback_query.message.edit_text("🏠 القائمة الرئيسية", reply_markup=main_menu_keyboard())

@router.callback_query(F.data == "menu_exchanges")
async def menu_exchanges(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Binance", callback_data="exchange_binance"))
    kb.add(types.InlineKeyboardButton("🔙 العودة", callback_data="back_main"))
    await callback_query.message.edit_text("💹 اختر المنصة:", reply_markup=kb)
    await state.set_state(ExchangeStates.choosing_exchange)

@router.callback_query(F.data.startswith("exchange_"), StateFilter(ExchangeStates.choosing_exchange))
async def select_exchange(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    exchange_name = callback_query.data.split("_")[1].capitalize()
    await state.set_state(ExchangeStates.entering_api_key)
    await state.update_data(exchange_name=exchange_name)
    await callback_query.message.edit_text(f"🔑 أدخل API Key لـ {exchange_name}:", reply_markup=back_keyboard())

@router.message(ExchangeStates.entering_api_key)
async def enter_api_key(message: types.Message, state: FSMContext):
    await state.update_data(api_key=message.text.strip())
    await state.set_state(ExchangeStates.entering_secret)
    await message.answer("🔒 أدخل Secret Key:", reply_markup=back_keyboard())

@router.message(ExchangeStates.entering_secret)
async def enter_secret(message: types.Message, state: FSMContext):
    await state.update_data(secret=message.text.strip())
    await state.set_state(ExchangeStates.entering_password)
    await message.answer("🔑 أدخل Password (أو 'لا' إذا لم يكن موجوداً):", reply_markup=back_keyboard())

@router.message(ExchangeStates.entering_password)
async def enter_password(message: types.Message, state: FSMContext):
    data = await state.get_data()
    password = message.text.strip() if message.text.strip().lower() != "لا" else None
    with db_session() as db:
        user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
        if user:
            db.query(ExchangeCredential).filter_by(user_id=user.id, exchange_id=data['exchange_name']).delete()
            exchange = ExchangeCredential(user_id=user.id, exchange_id=data['exchange_name'], api_key=data['api_key'], secret=data['secret'], password=password)
            db.add(exchange)
    await state.clear()
    await message.answer("✅ تم حفظ بيانات المنصة بنجاح!", reply_markup=main_menu_keyboard())

@router.callback_query(F.data == "menu_investment")
async def menu_investment(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await state.set_state(InvestmentStates.entering_amount)
    await callback_query.message.edit_text("💵 أدخل مبلغ الاستثمار (الحد الأدنى 5 USDT):", reply_markup=back_keyboard())

@router.message(InvestmentStates.entering_amount)
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
        await state.clear()
        await message.answer(f"✅ تم تعيين مبلغ الاستثمار إلى {amount:.2f} USDT", reply_markup=main_menu_keyboard())
    except ValueError:
        await message.answer("❌ صيغة المبلغ غير صحيحة. يرجى إدخال رقم:")

@router.callback_query(F.data == "menu_settings")
async def menu_settings(callback_query: types.CallbackQuery):
    await callback_query.answer()
    await callback_query.message.edit_text("⚙️ إعدادات التداول:", reply_markup=settings_keyboard())

@router.callback_query(F.data.startswith("setting_"))
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

@router.callback_query(F.data == "menu_start_trading")
async def menu_start_trading(callback_query: types.CallbackQuery):
    await callback_query.answer()
    with db_session() as db:
        user = db.query(User).filter_by(telegram_id=callback_query.from_user.id).first()
        if user:
            if user.investment_status == "running":
                await callback_query.message.answer("البوت يعمل بالفعل. يمكنك إيقافه من القائمة الرئيسية.")
                return
            user.investment_status = "running"
            await callback_query.message.edit_text("🚀 بدء التداول...", reply_markup=main_menu_keyboard())
            # Start the trading cycle in a background task
            asyncio.create_task(enhanced_trading_cycle(user.telegram_id, callback_query.bot))

@router.callback_query(F.data == "menu_stop_bot")
async def menu_stop_bot(callback_query: types.CallbackQuery):
    await callback_query.answer()
    with db_session() as db:
        user = db.query(User).filter_by(telegram_id=callback_query.from_user.id).first()
        if user:
            user.investment_status = "stopped"
    await callback_query.message.edit_text("🛑 تم إيقاف البوت. لن يتم تنفيذ أي عمليات جديدة.", reply_markup=main_menu_keyboard())

@router.callback_query(F.data == "menu_report")
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
# Main Function
# -----------------
async def main():
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()
    dp.include_router(router)
    
    logger.info("Starting bot...")
    upgrade_database()
    logger.info("Database tables checked/upgraded successfully.")

    await dp.start_polling(bot, storage=MemoryStorage())

if __name__ == '__main__':
    asyncio.run(main())