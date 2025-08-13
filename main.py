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

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, BigInteger
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
            
            # هنا يتم تنفيذ منطق المراجحة الفعلي
            # هذا مثال مبسط للتوضيح فقط
            
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
