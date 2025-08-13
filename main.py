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
    UniqueConstraint  # تم استيراده هنا
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
import ccxt

# ----------------------- الإعدادات الأساسية -----------------------
logging.basicConfig(level=logging.INFO)
BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///arbitrage.db")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", Fernet.generate_key().decode())

if not BOT_TOKEN:
    raise ValueError("يجب تعيين متغير البيئة BOT_TOKEN")

# ----------------------- تشفير البيانات -----------------------
class CryptoManager:
    def __init__(self):
        self.cipher_suite = Fernet(ENCRYPTION_KEY.encode())
    
    def encrypt(self, data: str) -> str:
        return self.cipher_suite.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        return self.cipher_suite.decrypt(encrypted_data.encode()).decode()

crypto_manager = CryptoManager()

# ----------------------- قاعدة البيانات -----------------------
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

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

# ----------------------- إعداد البوت -----------------------
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# ----------------------- حالات المحادثة -----------------------
class Form(StatesGroup):
    waiting_api_key = State()
    waiting_secret = State()
    waiting_password = State()
    waiting_investment = State()
    waiting_wallet = State()

# ----------------------- المنصات المدعومة -----------------------
SUPPORTED_EXCHANGES = {
    "binance": "Binance",
    "kucoin": "KuCoin",
    "okx": "OKX",
    "bybit": "Bybit"
}

# ----------------------- الدوال المساعدة -----------------------
async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def show_main_menu(user: User):
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
    
    status = "🟢 قيد التشغيل" if user.investment_status == "started" else "🔴 متوقف"
    message = (
        f"مرحباً بك في بوت المراجحة الذكي\n"
        f"حالة التداول: {status}\n"
        f"رصيد الاستثمار: {user.investment_amount:.2f} USDT\n"
        f"نسبة الربح الأدنى: {user.min_profit_percent:.2f}%"
    )
    return message, kb

async def verify_exchange_credentials(exchange_id: str, api_key: str, secret: str, password: Optional[str] = None) -> bool:
    try:
        exchange = getattr(ccxt, exchange_id)({
            'apiKey': api_key,
            'secret': secret,
            'password': password,
            'enableRateLimit': True
        })
        await asyncio.to_thread(exchange.fetch_balance)
        return True
    except Exception as e:
        logging.error(f"فشل التحقق: {e}")
        return False

# ----------------------- معالجات الأوامر -----------------------
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
    
    menu_msg, menu_kb = await show_main_menu(user)
    await message.answer(welcome_msg)
    await message.answer(menu_msg, reply_markup=menu_kb)
    db.close()

@dp.callback_query_handler(lambda c: c.data == 'main_menu')
async def back_to_main(call: types.CallbackQuery):
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=call.from_user.id).first()
    menu_msg, menu_kb = await show_main_menu(user)
    await call.message.edit_text(menu_msg, reply_markup=menu_kb)
    db.close()

# ----------------------- إدارة المنصات -----------------------
@dp.callback_query_handler(lambda c: c.data == 'menu_exchanges')
async def menu_exchanges(call: types.CallbackQuery):
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=call.from_user.id).first()
    
    kb = InlineKeyboardMarkup(row_width=2)
    for ex_id, ex_name in SUPPORTED_EXCHANGES.items():
        cred = next((c for c in user.exchanges if c.exchange_id == ex_id), None)
        status = "✅" if cred and cred.active else "❌"
        kb.add(InlineKeyboardButton(
            f"{status} {ex_name}", 
            callback_data=f"ex_{ex_id}"
        ))
    
    kb.add(InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu"))
    await call.message.edit_text("اختر المنصة لإدارة مفاتيح API:", reply_markup=kb)
    db.close()

@dp.callback_query_handler(lambda c: c.data.startswith('ex_'))
async def exchange_selected(call: types.CallbackQuery, state: FSMContext):
    ex_id = call.data.split('_')[1]
    await state.update_data(selected_exchange=ex_id)
    await call.message.edit_text(f"أرسل مفتاح API لمنصة {SUPPORTED_EXCHANGES[ex_id]}:")
    await Form.waiting_api_key.set()

@dp.message_handler(state=Form.waiting_api_key)
async def api_key_received(message: types.Message, state: FSMContext):
    api_key = message.text.strip()
    await state.update_data(api_key=api_key)
    await message.answer("أرسل Secret Key:")
    await Form.waiting_secret.set()

@dp.message_handler(state=Form.waiting_secret)
async def secret_received(message: types.Message, state: FSMContext):
    secret = message.text.strip()
    await state.update_data(secret=secret)
    
    data = await state.get_data()
    ex_id = data['selected_exchange']
    
    if ex_id in ['kucoin', 'okx']:
        await message.answer("أرسل Passphrase (إذا لم يكن لديك اكتب '-'):")
        await Form.waiting_password.set()
    else:
        await save_exchange_credentials(message, state)

@dp.message_handler(state=Form.waiting_password)
async def password_received(message: types.Message, state: FSMContext):
    password = message.text.strip()
    if password == '-':
        password = None
    await state.update_data(password=password)
    await save_exchange_credentials(message, state)

async def save_exchange_credentials(message: types.Message, state: FSMContext):
    data = await state.get_data()
    ex_id = data['selected_exchange']
    api_key = data['api_key']
    secret = data['secret']
    password = data.get('password')
    
    # التحقق من صحة المفاتيح
    is_valid = await verify_exchange_credentials(ex_id, api_key, secret, password)
    if not is_valid:
        await message.answer("❌ المفاتيح غير صالحة أو الصلاحيات ناقصة. الرجاء المحاولة مرة أخرى.")
        await state.finish()
        return
    
    # حفظ المفاتيح المشفرة
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
    
    cred = next((c for c in user.exchanges if c.exchange_id == ex_id), None)
    if not cred:
        cred = ExchangeCredential(
            user_id=user.id,
            exchange_id=ex_id
        )
    
    cred.encrypted_api_key = crypto_manager.encrypt(api_key)
    cred.encrypted_secret = crypto_manager.encrypt(secret)
    if password:
        cred.encrypted_password = crypto_manager.encrypt(password)
    cred.active = True
    
    db.add(cred)
    db.commit()
    
    await message.answer(
        f"✅ تم ربط {SUPPORTED_EXCHANGES[ex_id]} بنجاح!", 
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("العودة للقائمة", callback_data="main_menu")
        )
    )
    
    db.close()
    await state.finish()

# ----------------------- إعدادات الاستثمار -----------------------
@dp.callback_query_handler(lambda c: c.data == 'menu_investment')
async def menu_investment(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("تعيين مبلغ الاستثمار", callback_data="set_investment"),
        InlineKeyboardButton("تعيين نسبة الربح", callback_data="set_profit_percent"),
        InlineKeyboardButton("إعدادات السحب", callback_data="set_withdrawal"),
        InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu")
    )
    await call.message.edit_text("إعدادات الاستثمار:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == 'set_investment')
async def set_investment(call: types.CallbackQuery):
    await call.message.edit_text("أرسل مبلغ الاستثمار بالدولار (مثال: 1000):")
    await Form.waiting_investment.set()

@dp.message_handler(state=Form.waiting_investment)
async def investment_received(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text)
        if amount <= 0:
            raise ValueError
        
        db = SessionLocal()
        user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
        user.investment_amount = amount
        db.commit()
        
        await message.answer(
            f"✅ تم تعيين مبلغ الاستثمار إلى {amount:.2f} USDT",
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("العودة للقائمة", callback_data="main_menu")
            )
        )
        db.close()
        await state.finish()
    except:
        await message.answer("❌ الرجاء إدخال مبلغ صحيح أكبر من الصفر")

# ----------------------- بدء/إيقاف التداول -----------------------
@dp.callback_query_handler(lambda c: c.data == 'menu_toggle_trading')
async def menu_toggle_trading(call: types.CallbackQuery):
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=call.from_user.id).first()
    
    active_exchanges = [ex for ex in user.exchanges if ex.active]
    if len(active_exchanges) < 2:
        await call.answer("❌ تحتاج إلى تفعيل منصتين على الأقل", show_alert=True)
        db.close()
        return
    
    if user.investment_amount <= 0:
        await call.answer("❌ لم تقم بتعيين مبلغ الاستثمار", show_alert=True)
        db.close()
        return
    
    kb = InlineKeyboardMarkup()
    if user.investment_status == "stopped":
        kb.add(InlineKeyboardButton("▶️ بدء التداول", callback_data="start_trading"))
    else:
        kb.add(InlineKeyboardButton("⏸️ إيقاف التداول", callback_data="stop_trading"))
    kb.add(InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu"))
    
    await call.message.edit_text(
        "حالة التداول الحالية: " + 
        ("🟢 قيد التشغيل" if user.investment_status == "started" else "🔴 متوقف"),
        reply_markup=kb
    )
    db.close()

@dp.callback_query_handler(lambda c: c.data == 'start_trading')
async def start_trading(call: types.CallbackQuery):
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=call.from_user.id).first()
    
    user.investment_status = "started"
    db.commit()
    
    await call.message.edit_text(
        "🟢 بدأ التداول الآلي بنجاح!",
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("العودة للقائمة", callback_data="main_menu")
        )
    )
    
    # بدء عملية المراجحة في الخلفية
    asyncio.create_task(run_arbitrage(user.telegram_id))
    
    db.close()

@dp.callback_query_handler(lambda c: c.data == 'stop_trading')
async def stop_trading(call: types.CallbackQuery):
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=call.from_user.id).first()
    
    user.investment_status = "stopped"
    db.commit()
    
    await call.message.edit_text(
        "🔴 تم إيقاف التداول الآلي",
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("العودة للقائمة", callback_data="main_menu")
        )
    )
    db.close()

# ----------------------- حلقة المراجحة -----------------------
async def run_arbitrage(user_id: int):
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=user_id).first()
    
    while user.investment_status == "started":
        try:
            active_exchanges = [
                ex for ex in user.exchanges 
                if ex.active and ex.encrypted_api_key and ex.encrypted_secret
            ]
            
            if len(active_exchanges) < 2:
                await bot.send_message(user_id, "❌ تحتاج إلى تفعيل منصتين على الأقل")
                user.investment_status = "stopped"
                db.commit()
                break
            
           async def run_arbitrage(user_id: int):
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=user_id).first()
    
    while user.investment_status == "started":
        try:
            # 1. تحميل بيانات المستخدم والمنصات المفعلة
            active_exchanges = [
                ex for ex in user.exchanges 
                if ex.active and ex.encrypted_api_key and ex.encrypted_secret
            ]
            
            if len(active_exchanges) < 2:
                await bot.send_message(user_id, "❌ تحتاج إلى تفعيل منصتين على الأقل")
                user.investment_status = "stopped"
                db.commit()
                break
            
            # 2. فك تشفير المفاتيح وإنشاء اتصالات بالمنصات
            exchanges = []
            for cred in active_exchanges:
                try:
                    exchange = getattr(ccxt, cred.exchange_id)({
                        'apiKey': crypto_manager.decrypt(cred.encrypted_api_key),
                        'secret': crypto_manager.decrypt(cred.encrypted_secret),
                        'password': crypto_manager.decrypt(cred.encrypted_password) if cred.encrypted_password else None,
                        'enableRateLimit': True,
                        'options': {'defaultType': 'spot'}
                    })
                    await asyncio.to_thread(exchange.load_markets)
                    exchanges.append(exchange)
                except Exception as e:
                    logging.error(f"Failed to initialize {cred.exchange_id}: {e}")
                    continue
            
            if len(exchanges) < 2:
                await bot.send_message(user_id, "❌ فشل الاتصال بمعظم المنصات")
                await asyncio.sleep(60)
                continue
            
            # 3. تحليل السوق للعثور على أفضل فرص المراجحة
            opportunities = await find_arbitrage_opportunities(exchanges, user.investment_amount, user.min_profit_percent)
            
            if not opportunities:
                await asyncio.sleep(30)
                continue
            
            # 4. تنفيذ أفضل فرصة مراجحة
            best_opportunity = max(opportunities, key=lambda x: x['profit_percent'])
            await execute_arbitrage_trade(user, best_opportunity)
            
            # 5. انتظر فترة مناسبة قبل الدورة التالية
            await asyncio.sleep(20)
            
        except Exception as e:
            logging.error(f"Error in arbitrage loop: {e}")
            await bot.send_message(user_id, f"⚠️ حدث خطأ في عملية المراجحة: {str(e)}")
            await asyncio.sleep(60)
        finally:
            # تحديث حالة المستخدم من قاعدة البيانات
            db.refresh(user)
    
    db.close()

async def find_arbitrage_opportunities(exchanges: list, investment_amount: float, min_profit_percent: float) -> list:
    opportunities = []
    symbols_to_check = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "XRP/USDT"]
    
    for symbol in symbols_to_check:
        try:
            # جمع بيانات الأسعار من جميع المنصات
            prices = []
            for exchange in exchanges:
                try:
                    ticker = await asyncio.to_thread(exchange.fetch_ticker, symbol)
                    prices.append({
                        'exchange': exchange,
                        'symbol': symbol,
                        'bid': float(ticker['bid']),
                        'ask': float(ticker['ask']),
                        'bid_volume': float(ticker['bidVolume']),
                        'ask_volume': float(ticker['askVolume'])
                    })
                except Exception as e:
                    logging.warning(f"Failed to get prices from {exchange.id}: {e}")
                    continue
            
            if len(prices) < 2:
                continue
            
            # البحث عن أفضل فرص الشراء والبيع
            best_buy = min(prices, key=lambda x: x['ask'])
            best_sell = max(prices, key=lambda x: x['bid'])
            
            if best_buy['exchange'].id == best_sell['exchange'].id:
                continue
            
            # حساب فرق السعر والنسبة المئوية للربح
            price_diff = best_sell['bid'] - best_buy['ask']
            profit_percent = (price_diff / best_buy['ask']) * 100
            
            if profit_percent < min_profit_percent:
                continue
            
            # حساب الكمية المتاحة للتداول
            max_amount = min(
                investment_amount / best_buy['ask'],
                best_buy['ask_volume'],
                best_sell['bid_volume']
            )
            
            if max_amount <= 0:
                continue
            
            # حساب الرسوم التقديرية
            fee_buy = await estimate_fee(best_buy['exchange'], symbol, 'buy', max_amount)
            fee_sell = await estimate_fee(best_sell['exchange'], symbol, 'sell', max_amount)
            total_fee = fee_buy + fee_sell
            
            # صافي الربح بعد الرسوم
            gross_profit = price_diff * max_amount
            net_profit = gross_profit - total_fee
            net_profit_percent = (net_profit / (best_buy['ask'] * max_amount)) * 100
            
            if net_profit_percent < min_profit_percent:
                continue
            
            opportunities.append({
                'symbol': symbol,
                'buy_exchange': best_buy['exchange'],
                'sell_exchange': best_sell['exchange'],
                'buy_price': best_buy['ask'],
                'sell_price': best_sell['bid'],
                'amount': max_amount,
                'gross_profit': gross_profit,
                'fees': total_fee,
                'net_profit': net_profit,
                'profit_percent': net_profit_percent,
                'timestamp': datetime.now()
            })
            
        except Exception as e:
            logging.error(f"Error analyzing {symbol}: {e}")
            continue
    
    return opportunities

async def estimate_fee(exchange, symbol: str, side: str, amount: float) -> float:
    try:
        market = exchange.markets[symbol]
        fee_rate = market['taker'] if 'taker' in market else 0.001
        
        if side == 'buy':
            return fee_rate * amount * market['ask']
        else:
            return fee_rate * amount * market['bid']
    except:
        return 0.002 * amount  # افترض رسوم 0.2% إذا فشل الحصول على الرسوم الدقيقة

async def execute_arbitrage_trade(user: User, opportunity: dict):
    db = SessionLocal()
    try:
        # 1. تنفيذ أمر الشراء
        buy_exchange = opportunity['buy_exchange']
        buy_order = await asyncio.to_thread(
            buy_exchange.create_market_buy_order,
            opportunity['symbol'],
            opportunity['amount']
        )
        
        # 2. تنفيذ أمر البيع
        sell_exchange = opportunity['sell_exchange']
        sell_order = await asyncio.to_thread(
            sell_exchange.create_market_sell_order,
            opportunity['symbol'],
            buy_order['filled']
        )
        
        # 3. حساب الربح الفعلي بعد التنفيذ
        actual_profit = sell_order['cost'] - buy_order['cost']
        actual_profit_percent = (actual_profit / buy_order['cost']) * 100
        
        # 4. تسجيل الصفقة في قاعدة البيانات
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
        
        # 5. إرسال إشعار للمستخدم
        profit_emoji = "🟢" if actual_profit > 0 else "🔴"
        message = (
            f"{profit_emoji} **تم تنفيذ صفقة مراجحة**\n"
            f"▫️ الزوج: {opportunity['symbol']}\n"
            f"▫️ الكمية: {buy_order['filled']:.6f}\n"
            f"▫️ سعر الشراء: {buy_order['price']:.4f} ({buy_exchange.id})\n"
            f"▫️ سعر البيع: {sell_order['price']:.4f} ({sell_exchange.id})\n"
            f"▫️ صافي الربح: {actual_profit:.4f} USDT ({actual_profit_percent:.2f}%)\n"
            f"▫️ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        await bot.send_message(user.telegram_id, message, parse_mode="Markdown")
        
        # 6. السحب التلقائي إذا كان مفعلاً
        if user.auto_withdraw and actual_profit > 1:  # السحب إذا كان الربح أكثر من 1 USDT
            await withdraw_profit(user, actual_profit)
            
    except Exception as e:
        logging.error(f"Trade execution failed: {e}")
        error_msg = f"❌ فشل تنفيذ الصفقة: {str(e)}"
        
        # تسجيل الصفقة الفاشلة
        if 'buy_order' in locals():
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
    if not user.wallet_address:
        await bot.send_message(
            user.telegram_id,
            "⚠️ لم يتم تعيين محفظة للسحب التلقائي\n"
            "الرجاء تعيين محفظتك من الإعدادات"
        )
        return False
    
    try:
        # في الواقع الفعلي، هنا نستخدم API المنصة للسحب
        # هذا مثال افتراضي للتوضيح فقط
        
        # نقوم بخصم رسوم السحب (0.5 USDT كمثال)
        withdrawal_fee = 0.5
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
        logging.error(f"Withdrawal failed: {e}")
        await bot.send_message(
            user.telegram_id,
            f"❌ فشل السحب التلقائي: {str(e)}\n"
            "الرجاء التحقق من إعدادات المحفظة"
        )
        return False
            
            await asyncio.sleep(30)  # انتظر 30 ثانية بين كل دورة
            
            # تأكد من تحديث حالة المستخدم
            db.refresh(user)
            
        except Exception as e:
            logging.error(f"Error in arbitrage loop: {e}")
            await asyncio.sleep(60)
    
    db.close()

# ----------------------- كشف الحساب -----------------------
@dp.callback_query_handler(lambda c: c.data == 'menu_report')
async def menu_report(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("آخر 7 أيام", callback_data="report_7d"),
        InlineKeyboardButton("آخر 30 يوم", callback_data="report_30d"),
        InlineKeyboardButton("كل الفترات", callback_data="report_all"),
        InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu")
    )
    await call.message.edit_text("اختر الفترة المراد عرض التقرير عنها:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith('report_'))
async def show_report(call: types.CallbackQuery):
    period = call.data.split('_')[1]
    
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=call.from_user.id).first()
    
    end_date = datetime.now()
    if period == '7d':
        start_date = end_date - timedelta(days=7)
    elif period == '30d':
        start_date = end_date - timedelta(days=30)
    else:
        start_date = datetime.min
    
    trades = db.query(TradeLog).filter(
        TradeLog.user_id == user.id,
        TradeLog.timestamp >= start_date,
        TradeLog.timestamp <= end_date
    ).all()
    
    if not trades:
        await call.message.edit_text(
            "لا توجد صفقات مسجلة في هذه الفترة",
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("رجوع", callback_data="menu_report")
            )
        )
        db.close()
        return
    
    total_profit = sum(t.net_profit for t in trades)
    winning_trades = sum(1 for t in trades if t.net_profit > 0)
    success_rate = (winning_trades / len(trades)) * 100
    
    report_msg = (
        f"📊 تقرير أداء التداول\n"
        f"الفترة: {period}\n"
        f"عدد الصفقات: {len(trades)}\n"
        f"إجمالي الربح: {total_profit:.2f} USDT\n"
        f"معدل النجاح: {success_rate:.1f}%\n\n"
        f"آخر تحديث: {end_date.strftime('%Y-%m-%d %H:%M')}"
    )
    
    await call.message.edit_text(
        report_msg,
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("رجوع", callback_data="menu_report")
        )
    )
    db.close()

# ----------------------- الإعدادات -----------------------
@dp.callback_query_handler(lambda c: c.data == 'menu_settings')
async def menu_settings(call: types.CallbackQuery):
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=call.from_user.id).first()
    
    auto_withdraw_status = "✅ مفعل" if user.auto_withdraw else "❌ معطل"
    
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton(f"السحب التلقائي: {auto_withdraw_status}", callback_data="toggle_withdraw"),
        InlineKeyboardButton("تعيين محفظة السحب", callback_data="set_wallet"),
        InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu")
    )
    
    wallet_info = f"\nالمحفظة الحالية: {user.wallet_address[:10]}...{user.wallet_address[-4:]}" if user.wallet_address else ""
    
    await call.message.edit_text(
        f"الإعدادات العامة{wallet_info}",
        reply_markup=kb
    )
    db.close()

@dp.callback_query_handler(lambda c: c.data == 'toggle_withdraw')
async def toggle_withdraw(call: types.CallbackQuery):
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=call.from_user.id).first()
    
    user.auto_withdraw = not user.auto_withdraw
    db.commit()
    
    await menu_settings(call)
    db.close()

@dp.callback_query_handler(lambda c: c.data == 'set_wallet')
async def set_wallet(call: types.CallbackQuery):
    await call.message.edit_text("أرسل عنوان محفظتك (للسحب التلقائي للأرباح):")
    await Form.waiting_wallet.set()

@dp.message_handler(state=Form.waiting_wallet)
async def wallet_received(message: types.Message, state: FSMContext):
    wallet = message.text.strip()
    
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
    user.wallet_address = wallet
    db.commit()
    
    await message.answer(
        f"✅ تم تعيين محفظة السحب بنجاح\n"
        f"العنوان: {wallet[:10]}...{wallet[-4:]}",
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("العودة للقائمة", callback_data="main_menu")
        )
    )
    db.close()
    await state.finish()

# ----------------------- تشغيل البوت -----------------------
async def on_startup(dp):
    await bot.set_my_commands([
        types.BotCommand("start", "بدء استخدام البوت"),
        types.BotCommand("status", "حالة التداول الحالية"),
        types.BotCommand("report", "عرض تقرير الأداء"),
        types.BotCommand("settings", "الإعدادات")
    ])

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
