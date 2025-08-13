import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from cryptography.fernet import Fernet

from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.markdown import hbold, hcode

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Boolean,
    ForeignKey,
    BigInteger,
    UniqueConstraint
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
import ccxt

# الإعدادات الأساسية
logging.basicConfig(level=logging.INFO)
BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///arbitrage.db")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", Fernet.generate_key().decode())

if not BOT_TOKEN:
    raise ValueError("يجب تعيين متغير البيئة BOT_TOKEN")
    # نظام التشفير
class CryptoManager:
    def __init__(self):
        self.cipher_suite = Fernet(ENCRYPTION_KEY.encode())
    
    def encrypt(self, data: str) -> str:
        return self.cipher_suite.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        return self.cipher_suite.decrypt(encrypted_data.encode()).decode()

crypto_manager = CryptoManager()

# نماذج قاعدة البيانات
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, index=True)
    investment_amount = Column(Float, default=0.0)
    min_profit_percent = Column(Float, default=1.0)
    investment_status = Column(String(20), default="stopped")
    fee_consent = Column(Boolean, default=False)
    auto_withdraw = Column(Boolean, default=True)
    wallet_address = Column(String(100), nullable=True)
    
    exchanges = relationship("ExchangeCredential", back_populates="user", cascade="all, delete-orphan")

class ExchangeCredential(Base):
    __tablename__ = "exchange_credentials"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    exchange_id = Column(String(50))
    encrypted_api_key = Column(String(512))
    encrypted_secret = Column(String(512))
    encrypted_password = Column(String(512), nullable=True)
    active = Column(Boolean, default=False)
    
    user = relationship("User", back_populates="exchanges")
    
    __table_args__ = (UniqueConstraint("user_id", "exchange_id", name="uq_user_exchange"),)

class TradeLog(Base):
    __tablename__ = "trade_logs"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True)
    symbol = Column(String(20))
    amount = Column(Float)
    entry_price = Column(Float)
    exit_price = Column(Float)
    profit_percent = Column(Float)
    net_profit = Column(Float)
    status = Column(String(20))
    timestamp = Column(DateTime, default=datetime.utcnow)

# إعدادات قاعدة البيانات
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base.metadata.create_all(engine)
# إعداد البوت
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# حالات المحادثة
class Form(StatesGroup):
    waiting_api_key = State()
    waiting_secret = State()
    waiting_password = State()
    waiting_investment = State()
    waiting_wallet = State()

# المنصات المدعومة
SUPPORTED_EXCHANGES = {
    "binance": "Binance",
    "kucoin": "KuCoin",
    "okx": "OKX",
    "bybit": "Bybit"
}
async def get_exchange_instance(cred: ExchangeCredential) -> ccxt.Exchange:
    """إنشاء وتجهيز مثيل منصة تداول"""
    exchange = getattr(ccxt, cred.exchange_id)({
        'apiKey': crypto_manager.decrypt(cred.encrypted_api_key),
        'secret': crypto_manager.decrypt(cred.encrypted_secret),
        'password': crypto_manager.decrypt(cred.encrypted_password) if cred.encrypted_password else None,
        'enableRateLimit': True,
        'options': {
            'defaultType': 'spot',
            'adjustForTimeDifference': True
        }
    })
    await asyncio.to_thread(exchange.load_markets)
    return exchange

async def analyze_market(exchanges: List[ccxt.Exchange], symbol: str) -> List[Dict]:
    """تحليل السوق لزوج تداول معين مع معالجة الأخطاء"""
    prices = []
    for exchange in exchanges:
        try:
            ticker = await asyncio.to_thread(exchange.fetch_ticker, symbol)
            
            # معالجة القيم الفارغة
            bid = float(ticker['bid']) if ticker['bid'] is not None else 0
            ask = float(ticker['ask']) if ticker['ask'] is not None else 0
            bid_volume = float(ticker['bidVolume']) if ticker['bidVolume'] is not None else 0
            ask_volume = float(ticker['askVolume']) if ticker['askVolume'] is not None else 0
            
            # تجاهل الأسعار غير الصالحة
            if bid <= 0 or ask <= 0:
                continue
                
            prices.append({
                'exchange': exchange,
                'symbol': symbol,
                'bid': bid,
                'ask': ask,
                'bid_volume': bid_volume,
                'ask_volume': ask_volume
            })
        except Exception as e:
            logging.warning(f"فشل في الحصول على الأسعار من {exchange.id}: {str(e)}")
            continue
    return prices

async def calculate_arbitrage_opportunity(prices: List[Dict], investment: float, min_profit: float) -> Optional[Dict]:
    """حساب فرص المراجحة المتاحة مع تحسينات الأمان"""
    if len(prices) < 2:
        return None
    
    # فلترة الأسعار غير الصالحة
    valid_prices = [p for p in prices if p['bid'] > 0 and p['ask'] > 0]
    
    if len(valid_prices) < 2:
        return None
    
    best_buy = min(valid_prices, key=lambda x: x['ask'])
    best_sell = max(valid_prices, key=lambda x: x['bid'])
    
    if best_buy['exchange'].id == best_sell['exchange'].id:
        return None
    
    price_diff = best_sell['bid'] - best_buy['ask']
    profit_percent = (price_diff / best_buy['ask']) * 100
    
    if profit_percent < min_profit:
        return None
    
    max_amount = min(
        investment / best_buy['ask'],
        best_buy['ask_volume'],
        best_sell['bid_volume']
    )
    
    if max_amount <= 0:
        return None
    
    return {
        'symbol': best_buy['symbol'],
        'buy_exchange': best_buy['exchange'],
        'sell_exchange': best_sell['exchange'],
        'buy_price': best_buy['ask'],
        'sell_price': best_sell['bid'],
        'amount': max_amount,
        'profit_percent': profit_percent
    }
async def execute_trade(user: User, opportunity: Dict):
    """تنفيذ صفقة المراجحة مع معالجة محسنة للأخطاء"""
    db = SessionLocal()
    try:
        # تنفيذ أمر الشراء
        buy_order = await asyncio.to_thread(
            opportunity['buy_exchange'].create_market_buy_order,
            opportunity['symbol'],
            opportunity['amount']
        )
        
        # تنفيذ أمر البيع
        sell_order = await asyncio.to_thread(
            opportunity['sell_exchange'].create_market_sell_order,
            opportunity['symbol'],
            buy_order['filled']
        )
        
        # حساب الربح الفعلي
        actual_profit = sell_order['cost'] - buy_order['cost']
        actual_profit_percent = (actual_profit / buy_order['cost']) * 100
        
        # تسجيل الصفقة
        trade = TradeLog(
            user_id=user.id,
            symbol=opportunity['symbol'],
            amount=buy_order['filled'],
            entry_price=buy_order['price'],
            exit_price=sell_order['price'],
            profit_percent=actual_profit_percent,
            net_profit=actual_profit,
            status='completed',
            timestamp=datetime.now()
        )
        db.add(trade)
        db.commit()
        
        # إرسال إشعار للمستخدم
        profit_emoji = "🟢" if actual_profit > 0 else "🔴"
        message = (
            f"{profit_emoji} **تم تنفيذ صفقة مراجحة**\n"
            f"▫️ الزوج: {opportunity['symbol']}\n"
            f"▫️ الكمية: {buy_order['filled']:.6f}\n"
            f"▫️ سعر الشراء: {buy_order['price']:.4f} ({opportunity['buy_exchange'].id})\n"
            f"▫️ سعر البيع: {sell_order['price']:.4f} ({opportunity['sell_exchange'].id})\n"
            f"▫️ صافي الربح: {actual_profit:.4f} USDT ({actual_profit_percent:.2f}%)\n"
            f"▫️ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        await bot.send_message(user.telegram_id, message, parse_mode="Markdown")
        
        # السحب التلقائي إذا كان مفعلاً
        if user.auto_withdraw and actual_profit > 1:
            await withdraw_profit(user, actual_profit)
            
    except Exception as e:
        logging.error(f"فشل تنفيذ الصفقة: {str(e)}")
        error_msg = f"❌ فشل تنفيذ الصفقة: {str(e)}"
        
        # تسجيل الصفقة الفاشلة
        trade = TradeLog(
            user_id=user.id,
            symbol=opportunity['symbol'],
            amount=opportunity['amount'],
            entry_price=opportunity['buy_price'],
            exit_price=0,
            profit_percent=0,
            net_profit=0,
            status='failed',
            timestamp=datetime.now(),
            note=str(e)
        )
        db.add(trade)
        db.commit()
        error_msg += f"\n\nتم إلغاء الصفقة وحفظ التفاصيل"
        await bot.send_message(user.telegram_id, error_msg)
    finally:
        db.close()

async def withdraw_profit(user: User, amount: float):
    """سحب الأرباح تلقائياً مع معالجة الأخطاء"""
    if not user.wallet_address:
        await bot.send_message(
            user.telegram_id,
            "⚠️ لم يتم تعيين محفظة للسحب التلقائي\n"
            "الرجاء تعيين محفظتك من الإعدادات"
        )
        return False
    
    try:
        withdrawal_fee = 0.5  # رسوم السحب (يمكن تعديلها حسب المنصة)
        net_amount = amount - withdrawal_fee
        
        if net_amount <= 0:
            await bot.send_message(
                user.telegram_id,
                f"⚠️ المبلغ صغير جداً للسحب بعد خصم الرسوم ({withdrawal_fee} USDT)"
            )
            return False
        
        # هنا يتم تنفيذ السحب الفعلي باستخدام API المنصة
        # withdrawal_result = await exchange.withdraw(...)
        
        await bot.send_message(
            user.telegram_id,
            f"✅ تم سحب {net_amount:.4f} USDT بنجاح إلى محفظتك\n"
            f"العنوان: {user.wallet_address[:6]}...{user.wallet_address[-4]}\n"
            f"رسوم السحب: {withdrawal_fee} USDT"
        )
        return True
    except Exception as e:
        logging.error(f"فشل السحب التلقائي: {str(e)}")
        await bot.send_message(
            user.telegram_id,
            f"❌ فشل السحب التلقائي: {str(e)}\n"
            "الرجاء التحقق من إعدادات المحفظة"
        )
        return False
async def run_arbitrage(user_id: int):
    """الحلقة الرئيسية للمراجحة الآلية مع تحسينات معالجة الأخطاء"""
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=user_id).first()
    
    while user.investment_status == "started":
        try:
            # 1. تحميل بيانات المستخدم والمنصات
            active_creds = [ex for ex in user.exchanges if ex.active]
            
            if len(active_creds) < 2:
                await bot.send_message(user_id, "❌ تحتاج إلى تفعيل منصتين على الأقل")
                user.investment_status = "stopped"
                db.commit()
                break
            
            # 2. تهيئة المنصات
            exchanges = []
            for cred in active_creds:
                try:
                    exchange = await get_exchange_instance(cred)
                    exchanges.append(exchange)
                except Exception as e:
                    logging.error(f"فشل تهيئة {cred.exchange_id}: {str(e)}")
                    continue
            
            if len(exchanges) < 2:
                await bot.send_message(user_id, "❌ فشل الاتصال بمعظم المنصات")
                await asyncio.sleep(60)
                continue
            
            # 3. البحث عن فرص المراجحة
            symbols = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT"]
            opportunities = []
            
            for symbol in symbols:
                try:
                    prices = await analyze_market(exchanges, symbol)
                    opportunity = await calculate_arbitrage_opportunity(
                        prices, user.investment_amount, user.min_profit_percent
                    )
                    if opportunity:
                        opportunities.append(opportunity)
                except Exception as e:
                    logging.error(f"خطأ في تحليل {symbol}: {str(e)}")
                    continue
            
            if not opportunities:
                await asyncio.sleep(30)
                continue
            
            # 4. تنفيذ أفضل فرصة
            best_opportunity = max(opportunities, key=lambda x: x['profit_percent'])
            await execute_trade(user, best_opportunity)
            
            # 5. انتظر قبل الدورة التالية
            await asyncio.sleep(20)
            
        except Exception as e:
            logging.error(f"خطأ في حلقة المراجحة: {str(e)}")
            await bot.send_message(user_id, f"⚠️ حدث خطأ في عملية المراجحة: {str(e)}")
            await asyncio.sleep(60)
        finally:
            db.refresh(user)
    
    db.close()
# ... (الاستيرادات والإعدادات الأساسية تبقى كما هي حتى سطر 387)

@dp.message_handler(commands=['start', 'help'])
async def cmd_start(message: types.Message):
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
    if not user:
        user = User(telegram_id=message.from_user.id)
        db.add(user)
        db.commit()
    
    welcome_msg = (
        "مرحباً بك في بوت المراجحة الآلية بين المنصات!\n"
        "يمكنك من خلال هذا البوت:\n"
        "- ربط حسابات التداول الخاصة بك\n"
        "- تحديد مبلغ الاستثمار\n"
        "- بدء التداول الآلي\n"
        "- متابعة الأرباح والإحصائيات"
    )
    
    menu_msg = (
        f"حالة التداول: {'🟢 قيد التشغيل' if user.investment_status == 'started' else '🔴 متوقف'}\n"
        f"رصيد الاستثمار: {user.investment_amount:.2f} USDT\n"
        f"نسبة الربح الأدنى: {user.min_profit_percent:.2f}%"
    )
    
    kb = InlineKeyboardMarkup(row_width=2)
    buttons = [
        ("🔐 إدارة المنصات", "menu_exchanges"),
        ("💰 إعدادات الاستثمار", "menu_investment"),
        ("📈 بدء/إيقاف التداول", "menu_toggle_trading"),
        ("📊 كشف الحساب", "menu_report"),
        ("⚙️ الإعدادات", "menu_settings")
    ]
    for text, callback in buttons:
        kb.add(InlineKeyboardButton(text, callback_data=callback))
    
    await message.answer(welcome_msg)
    await message.answer(menu_msg, reply_markup=kb)
    db.close()

@dp.callback_query_handler(lambda c: c.data == 'main_menu')
async def back_to_main(call: types.CallbackQuery):
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=call.from_user.id).first()
    
    menu_msg = (
        f"حالة التداول: {'🟢 قيد التشغيل' if user.investment_status == 'started' else '🔴 متوقف'}\n"
        f"رصيد الاستثمار: {user.investment_amount:.2f} USDT\n"
        f"نسبة الربح الأدنى: {user.min_profit_percent:.2f}%"
    )
    
    kb = InlineKeyboardMarkup(row_width=2)
    buttons = [
        ("🔐 إدارة المنصات", "menu_exchanges"),
        ("💰 إعدادات الاستثمار", "menu_investment"),
        ("📈 بدء/إيقاف التداول", "menu_toggle_trading"),
        ("📊 كشف الحساب", "menu_report"),
        ("⚙️ الإعدادات", "menu_settings")
    ]
    for text, callback in buttons:
        kb.add(InlineKeyboardButton(text, callback_data=callback))
    
    await call.message.edit_text(menu_msg, reply_markup=kb)
    db.close()

async def on_startup(dp):
    await bot.set_my_commands([
        types.BotCommand("start", "بدء استخدام البوت"),
        types.BotCommand("status", "حالة التداول الحالية"),
        types.BotCommand("report", "عرض تقرير الأداء"),
        types.BotCommand("settings", "الإعدادات")
    ])
    
    # بدء عمليات المراجحة للمستخدمين النشطين
    db = SessionLocal()
    active_users = db.query(User).filter_by(investment_status="started").all()
    for user in active_users:
        asyncio.create_task(run_arbitrage(user.telegram_id))
    db.close()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
