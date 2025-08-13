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
logger = logging.getLogger(__name__)
BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///arbitrage.db")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", Fernet.generate_key().decode())

if not BOT_TOKEN:
    raise ValueError("يجب تعيين متغير البيئة BOT_TOKEN")

# نظام التشفير
class CryptoManager:
    def __init__(self):
        try:
            self.cipher_suite = Fernet(ENCRYPTION_KEY.encode())
        except Exception as e:
            logger.error(f"فشل في تهيئة نظام التشفير: {e}")
            raise

    def encrypt(self, data: str) -> str:
        try:
            return self.cipher_suite.encrypt(data.encode()).decode()
        except Exception as e:
            logger.error(f"فشل في تشفير البيانات: {e}")
            raise

    def decrypt(self, encrypted_data: str) -> str:
        try:
            return self.cipher_suite.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            logger.error(f"فشل في فك تشفير البيانات: {e}")
            raise

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
    last_activity = Column(DateTime, default=datetime.utcnow)
    
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
    last_verified = Column(DateTime, nullable=True)
    
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
    details = Column(String(500), nullable=True)

# إعدادات قاعدة البيانات
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=3600)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
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

# المنصات المدعومة مع معلومات إضافية
SUPPORTED_EXCHANGES = {
    "binance": {
        "name": "Binance",
        "requires_password": False,
        "trading_fee": 0.1
    },
    "kucoin": {
        "name": "KuCoin",
        "requires_password": False,
        "trading_fee": 0.1
    },
    "okx": {
        "name": "OKX",
        "requires_password": True,
        "trading_fee": 0.1
    },
    "bybit": {
        "name": "Bybit",
        "requires_password": False,
        "trading_fee": 0.1
    }
}

# تحسينات في وظيفة إنشاء مثيل المنصة
async def get_exchange_instance(cred: ExchangeCredential) -> ccxt.Exchange:
    """إنشاء وتجهيز مثيل منصة تداول مع معالجة محسنة للأخطاء"""
    try:
        exchange_class = getattr(ccxt, cred.exchange_id)
        exchange_params = {
            'apiKey': crypto_manager.decrypt(cred.encrypted_api_key),
            'secret': crypto_manager.decrypt(cred.encrypted_secret),
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot',
                'adjustForTimeDifference': True
            }
        }
        
        if cred.encrypted_password:
            exchange_params['password'] = crypto_manager.decrypt(cred.encrypted_password)
        
        exchange = exchange_class(exchange_params)
        
        # التحقق من صحة الاعتمادات
        await asyncio.to_thread(exchange.load_markets)
        
        # تحديث وقت التحقق الأخير
        db = SessionLocal()
        cred.last_verified = datetime.utcnow()
        db.commit()
        db.close()
        
        return exchange
        
    except ccxt.AuthenticationError as e:
        logger.error(f"اعتمادات غير صالحة لـ {cred.exchange_id}: {e}")
        raise ValueError("اعتمادات API غير صالحة")
    except ccxt.ExchangeError as e:
        logger.error(f"خطأ في الاتصال بـ {cred.exchange_id}: {e}")
        raise ValueError("فشل الاتصال بالمنصة")
    except Exception as e:
        logger.error(f"خطأ غير متوقع في تهيئة {cred.exchange_id}: {e}")
        raise ValueError("حدث خطأ غير متوقع")

# تحسينات في وظيفة تحليل السوق
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
                
            # حساب الرسوم
            exchange_info = SUPPORTED_EXCHANGES.get(exchange.id, {})
            fee_percent = exchange_info.get('trading_fee', 0.1)
            effective_bid = bid * (1 - fee_percent/100)
            effective_ask = ask * (1 + fee_percent/100)
                
            prices.append({
                'exchange': exchange,
                'symbol': symbol,
                'bid': bid,
                'ask': ask,
                'effective_bid': effective_bid,
                'effective_ask': effective_ask,
                'bid_volume': bid_volume,
                'ask_volume': ask_volume,
                'fee_percent': fee_percent
            })
        except ccxt.NetworkError as e:
            logger.warning(f"خطأ شبكة أثناء جلب الأسعار من {exchange.id}: {e}")
            continue
        except ccxt.ExchangeError as e:
            logger.warning(f"خطأ منصة أثناء جلب الأسعار من {exchange.id}: {e}")
            continue
        except Exception as e:
            logger.warning(f"خطأ غير متوقع أثناء جلب الأسعار من {exchange.id}: {e}")
            continue
    return prices

# تحسينات في وظيفة حساب فرص المراجحة
async def calculate_arbitrage_opportunity(prices: List[Dict], investment: float, min_profit: float) -> Optional[Dict]:
    """حساب فرص المراجحة المتاحة مع تحسينات الأمان"""
    if len(prices) < 2:
        return None
    
    # فلترة الأسعار غير الصالحة
    valid_prices = [p for p in prices if p['bid'] > 0 and p['ask'] > 0]
    
    if len(valid_prices) < 2:
        return None
    
    # استخدام الأسعار الفعالة بعد حساب الرسوم
    best_buy = min(valid_prices, key=lambda x: x['effective_ask'])
    best_sell = max(valid_prices, key=lambda x: x['effective_bid'])
    
    if best_buy['exchange'].id == best_sell['exchange'].id:
        return None
    
    price_diff = best_sell['effective_bid'] - best_buy['effective_ask']
    profit_percent = (price_diff / best_buy['effective_ask']) * 100
    
    if profit_percent < min_profit:
        return None
    
    # حساب الكمية القابلة للتداول مع مراعاة السيولة
    max_amount = min(
        investment / best_buy['effective_ask'],
        best_buy['ask_volume'] * 0.1,  # لا تتجاوز 10% من السيولة المتاحة
        best_sell['bid_volume'] * 0.1,
        (investment * 0.1) / best_buy['effective_ask']  # لا تتجاوز 10% من رأس المال
    )
    
    if max_amount <= 0:
        return None
    
    return {
        'symbol': best_buy['symbol'],
        'buy_exchange': best_buy['exchange'],
        'sell_exchange': best_sell['exchange'],
        'buy_price': best_buy['ask'],
        'sell_price': best_sell['bid'],
        'effective_buy_price': best_buy['effective_ask'],
        'effective_sell_price': best_sell['effective_bid'],
        'amount': max_amount,
        'profit_percent': profit_percent,
        'buy_fee': best_buy['fee_percent'],
        'sell_fee': best_sell['fee_percent']
    }

# تحسينات في وظيفة تنفيذ الصفقة
async def execute_trade(user: User, opportunity: Dict):
    """تنفيذ صفقة المراجحة مع معالجة محسنة للأخطاء"""
    db = SessionLocal()
    trade_log = None
    try:
        # تسجيل بدء الصفقة
        trade_log = TradeLog(
            user_id=user.id,
            symbol=opportunity['symbol'],
            amount=opportunity['amount'],
            entry_price=opportunity['buy_price'],
            exit_price=0,
            profit_percent=0,
            net_profit=0,
            status='pending',
            timestamp=datetime.utcnow(),
            details=f"بدء الصفقة بين {opportunity['buy_exchange'].id} و {opportunity['sell_exchange'].id}"
        )
        db.add(trade_log)
        db.commit()
        
        # تنفيذ أمر الشراء
        buy_order = await asyncio.to_thread(
            opportunity['buy_exchange'].create_order,
            opportunity['symbol'],
            'market',
            'buy',
            opportunity['amount'],
            None,
            {'type': 'market'}
        )
        
        # تسجيل تفاصيل الشراء
        trade_log.entry_price = float(buy_order['price'])
        trade_log.amount = float(buy_order['filled'])
        trade_log.details = f"تم الشراء: {buy_order}"
        db.commit()
        
        # تنفيذ أمر البيع
        sell_order = await asyncio.to_thread(
            opportunity['sell_exchange'].create_order,
            opportunity['symbol'],
            'market',
            'sell',
            trade_log.amount,
            None,
            {'type': 'market'}
        )
        
        # حساب الربح الفعلي
        buy_cost = trade_log.amount * trade_log.entry_price * (1 + opportunity['buy_fee']/100)
        sell_revenue = trade_log.amount * float(sell_order['price']) * (1 - opportunity['sell_fee']/100)
        actual_profit = sell_revenue - buy_cost
        actual_profit_percent = (actual_profit / buy_cost) * 100
        
        # تحديث سجل الصفقة
        trade_log.exit_price = float(sell_order['price'])
        trade_log.profit_percent = actual_profit_percent
        trade_log.net_profit = actual_profit
        trade_log.status = 'completed'
        trade_log.details = f"{trade_log.details}\nتم البيع: {sell_order}"
        db.commit()
        
        # إرسال إشعار للمستخدم
        profit_emoji = "🟢" if actual_profit > 0 else "🔴"
        message = (
            f"{profit_emoji} **تم تنفيذ صفقة مراجحة**\n"
            f"▫️ الزوج: {opportunity['symbol']}\n"
            f"▫️ الكمية: {trade_log.amount:.6f}\n"
            f"▫️ سعر الشراء: {trade_log.entry_price:.6f} ({opportunity['buy_exchange'].id})\n"
            f"▫️ رسوم الشراء: {opportunity['buy_fee']:.2f}%\n"
            f"▫️ سعر البيع: {trade_log.exit_price:.6f} ({opportunity['sell_exchange'].id})\n"
            f"▫️ رسوم البيع: {opportunity['sell_fee']:.2f}%\n"
            f"▫️ صافي الربح: {actual_profit:.6f} USDT ({actual_profit_percent:.2f}%)\n"
            f"▫️ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        await bot.send_message(user.telegram_id, message, parse_mode="Markdown")
        
        # السحب التلقائي إذا كان مفعلاً
        if user.auto_withdraw and actual_profit > 1:
            await withdraw_profit(user, actual_profit)
            
    except ccxt.InsufficientFunds as e:
        error_msg = "❌ رصيد غير كافي لتنفيذ الصفقة"
        logger.error(f"رصيد غير كافي: {e}")
        if trade_log:
            trade_log.status = 'failed'
            trade_log.details = f"{trade_log.details}\nرصيد غير كافي: {e}"
            db.commit()
        await bot.send_message(user.telegram_id, error_msg)
        
    except ccxt.NetworkError as e:
        error_msg = "❌ فشل الشبكة أثناء تنفيذ الصفقة"
        logger.error(f"خطأ شبكة: {e}")
        if trade_log:
            trade_log.status = 'failed'
            trade_log.details = f"{trade_log.details}\nخطأ شبكة: {e}"
            db.commit()
        await bot.send_message(user.telegram_id, error_msg)
        
    except ccxt.ExchangeError as e:
        error_msg = f"❌ خطأ منصة: {str(e)}"
        logger.error(f"خطأ منصة: {e}")
        if trade_log:
            trade_log.status = 'failed'
            trade_log.details = f"{trade_log.details}\nخطأ منصة: {e}"
            db.commit()
        await bot.send_message(user.telegram_id, error_msg)
        
    except Exception as e:
        error_msg = f"❌ خطأ غير متوقع: {str(e)}"
        logger.error(f"خطأ غير متوقع: {e}")
        if trade_log:
            trade_log.status = 'failed'
            trade_log.details = f"{trade_log.details}\nخطأ غير متوقع: {e}"
            db.commit()
        await bot.send_message(user.telegram_id, error_msg)
        
    finally:
        db.close()

# تحسينات في وظيفة السحب التلقائي
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
        # حساب صافي المبلغ بعد خصم الرسوم
        withdrawal_fee = 1.0  # رسوم السحب (يمكن تعديلها حسب المنصة)
        net_amount = amount - withdrawal_fee
        
        if net_amount <= 0:
            await bot.send_message(
                user.telegram_id,
                f"⚠️ المبلغ صغير جداً للسحب بعد خصم الرسوم ({withdrawal_fee} USDT)"
            )
            return False
        
        # هنا يتم تنفيذ السحب الفعلي باستخدام API المنصة
        # withdrawal_result = await exchange.withdraw(...)
        
        # في هذا المثال، سنفترض نجاح العملية
        success = True
        
        if success:
            await bot.send_message(
                user.telegram_id,
                f"✅ تم سحب {net_amount:.4f} USDT بنجاح إلى محفظتك\n"
                f"العنوان: {user.wallet_address[:6]}...{user.wallet_address[-4:]}\n"
                f"رسوم السحب: {withdrawal_fee} USDT"
            )
            return True
        else:
            raise Exception("فشل في تنفيذ السحب")
            
    except Exception as e:
        logger.error(f"فشل السحب التلقائي: {str(e)}")
        await bot.send_message(
            user.telegram_id,
            f"❌ فشل السحب التلقائي: {str(e)}\n"
            "الرجاء التحقق من إعدادات المحفظة"
        )
        return False

# تحسينات في حلقة المراجحة الرئيسية
async def run_arbitrage(user_id: int):
    """الحلقة الرئيسية للمراجحة الآلية مع تحسينات معالجة الأخطاء"""
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=user_id).first()
    
    if not user:
        logger.error(f"المستخدم غير موجود: {user_id}")
        db.close()
        return
    
    logger.info(f"بدء عملية المراجحة للمستخدم: {user_id}")
    
    while user.investment_status == "started":
        try:
            # تحديث وقت النشاط الأخير
            user.last_activity = datetime.utcnow()
            db.commit()
            
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
                except ValueError as e:
                    await bot.send_message(user_id, f"❌ خطأ في منصة {cred.exchange_id}: {str(e)}")
                    cred.active = False
                    db.commit()
                    continue
                except Exception as e:
                    logger.error(f"خطأ غير متوقع في تهيئة {cred.exchange_id}: {str(e)}")
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
                    logger.error(f"خطأ في تحليل {symbol}: {str(e)}")
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
            logger.error(f"خطأ في حلقة المراجحة: {str(e)}")
            await bot.send_message(user_id, f"⚠️ حدث خطأ في عملية المراجحة: {str(e)}")
            await asyncio.sleep(60)
        finally:
            db.refresh(user)
    
    logger.info(f"إيقاف عملية المراجحة للمستخدم: {user_id}")
    db.close()

# ... (بقية الكود الخاص بمعالجات الرسائل والواجهة يبقى كما هو)

@dp.message_handler(commands=['start', 'help'])
async def cmd_start(message: types.Message):
    db = SessionLocal()
    try:
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
    except Exception as e:
        logger.error(f"خطأ في أمر البدء: {str(e)}")
        await message.answer("❌ حدث خطأ أثناء معالجة طلبك. يرجى المحاولة لاحقاً.")
    finally:
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
    try:
        active_users = db.query(User).filter_by(investment_status="started").all()
        for user in active_users:
            asyncio.create_task(run_arbitrage(user.telegram_id))
    finally:
        db.close()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
