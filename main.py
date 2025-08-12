import os
import asyncio
import logging
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from binance.client import Client as BinanceClient
from kucoin.client import Market, Trade

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

if not BOT_TOKEN or not DATABASE_URL:
    raise Exception("❌ Missing environment variables BOT_TOKEN or DATABASE_URL")

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
    telegram_id = Column(Integer, unique=True, index=True)
    # API keys per platform
    binance_api = Column(String(256), nullable=True)
    binance_secret = Column(String(256), nullable=True)
    kucoin_api = Column(String(256), nullable=True)
    kucoin_secret = Column(String(256), nullable=True)
    kucoin_passphrase = Column(String(256), nullable=True)
    # Investment info
    investment_amount = Column(Float, default=0.0)
    investment_status = Column(String(20), default="stopped")  # started / stopped
    # Store which platforms are active
    binance_active = Column(Boolean, default=False)
    kucoin_active = Column(Boolean, default=False)

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

# ----------------------- FSM States -----------------------

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
        market_client = Market(user.kucoin_api, user.kucoin_secret, user.kucoin_passphrase)
        trade_client = Trade(user.kucoin_api, user.kucoin_secret, user.kucoin_passphrase)
        return market_client, trade_client
    return None, None

async def verify_binance_keys(api_key, secret_key):
    try:
        client = BinanceClient(api_key, secret_key)
        client.get_account()
        return True
    except Exception:
        return False

async def verify_kucoin_keys(api_key, secret_key, passphrase):
    try:
        market_client = Market(api_key, secret_key, passphrase)
        # تحقق من صلاحية المفاتيح باستخدام طلب بيانات الحساب
        account_info = market_client.get_account()
        return True
    except Exception as e:
        logging.error(f"خطأ في التحقق من مفاتيح KuCoin: {e}")
        return False

def user_platforms_keyboard(user: User):
    kb = InlineKeyboardMarkup(row_width=2)
    binance_text = ("✅ Binance" if user.binance_active else "❌ Binance") + (" (مربوط)" if user.binance_api else " (غير مربوط)")
    kucoin_text = ("✅ KuCoin" if user.kucoin_active else "❌ KuCoin") + (" (مربوط)" if user.kucoin_api else " (غير مربوط)")
    kb.insert(InlineKeyboardButton(binance_text, callback_data="platform_binance"))
    kb.insert(InlineKeyboardButton(kucoin_text, callback_data="platform_kucoin"))
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
        InlineKeyboardButton("❓ كيف تحصل على مفاتيح API", callback_data="menu_api_help"),
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

# 1- تسجيل/تعديل بيانات التداول
@dp.callback_query_handler(lambda c: c.data == "menu_edit_trading_data")
async def menu_edit_trading_data(call: types.CallbackQuery):
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=call.from_user.id).first()
    db.close()
    await call.answer()
    await call.message.edit_text(
        "اختر المنصة لإضافة/تعديل مفاتيح API أو تفعيل/إيقاف:",
        reply_markup=user_platforms_keyboard(user)
    )

@dp.callback_query_handler(lambda c: c.data.startswith("platform_"))
async def platform_selected(call: types.CallbackQuery, state: FSMContext):
    platform = call.data.split("_")[1]
    await state.update_data(selected_platform=platform)
    await call.answer()

    if platform == "binance":
        await call.message.edit_text("أرسل مفتاح API الخاص بمنصة Binance:")
        await Form.waiting_api_key.set()
    elif platform == "kucoin":
        await call.message.edit_text("أرسل مفتاح API الخاص بمنصة KuCoin:")
        await Form.waiting_api_key.set()

@dp.message_handler(state=Form.waiting_api_key)
async def api_key_received(message: types.Message, state: FSMContext):
    data = await state.get_data()
    platform = data["selected_platform"]
    api_key = message.text.strip()

    await state.update_data(api_key=api_key)

    if platform == "binance":
        await message.answer("أرسل الـ Secret Key الخاص بـ Binance:")
        await Form.waiting_secret_key.set()
    elif platform == "kucoin":
        await message.answer("أرسل الـ Secret Key الخاص بـ KuCoin:")
        await Form.waiting_secret_key.set()

@dp.message_handler(state=Form.waiting_secret_key)
async def secret_key_received(message: types.Message, state: FSMContext):
    data = await state.get_data()
    platform = data["selected_platform"]
    secret_key = message.text.strip()

    await state.update_data(secret_key=secret_key)

    if platform == "binance":
        valid = await verify_binance_keys(data["api_key"], secret_key)
        if not valid:
            await message.answer("❌ المفاتيح غير صحيحة، أرسل /start وحاول مرة أخرى.")
            await state.finish()
            return
        db = SessionLocal()
        user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
        user.binance_api = data["api_key"]
        user.binance_secret = secret_key
        user.binance_active = True
        db.add(user)
        db.commit()
        db.close()
        await message.answer("✅ تم ربط Binance بنجاح!")
        await state.finish()
        await message.answer("العودة للقائمة الرئيسية:", reply_markup=main_menu_keyboard())

    elif platform == "kucoin":
        await message.answer("أرسل الـ Passphrase الخاص بـ KuCoin:")
        await Form.waiting_passphrase.set()

@dp.message_handler(state=Form.waiting_passphrase)
async def passphrase_received(message: types.Message, state: FSMContext):
    data = await state.get_data()
    passphrase = message.text.strip()
    platform = data["selected_platform"]

    valid = await verify_kucoin_keys(data["api_key"], data["secret_key"], passphrase)
    if not valid:
        await message.answer(
            "❌ المفاتيح غير صحيحة أو لا تحتوي على الصلاحيات اللازمة.\n"
            "تأكد من تفعيل صلاحيات القراءة والتداول فقط، وأعد المحاولة."
        )
        await state.finish()
        return

    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
    user.kucoin_api = data["api_key"]
    user.kucoin_secret = data["secret_key"]
    user.kucoin_passphrase = passphrase
    user.kucoin_active = True
    db.add(user)
    db.commit()
    db.close()

    await message.answer("✅ تم ربط KuCoin بنجاح!")
    await state.finish()
    await message.answer("العودة للقائمة الرئيسية:", reply_markup=main_menu_keyboard())

# 1.1 تحديد مبلغ الاستثمار
@dp.callback_query_handler(lambda c: c.data == "menu_edit_investment_amount")
async def investment_amount_handler(call: types.CallbackQuery):
    await call.answer()
    await call.message.edit_text("أرسل مبلغ الاستثمار (مثلاً: 100):")
    await Form.waiting_investment_amount.set()

@dp.message_handler(state=Form.waiting_investment_amount)
async def investment_amount_received(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.strip())
        if amount <= 0:
            await message.answer("❌ المبلغ يجب أن يكون أكبر من صفر.")
            return
        db = SessionLocal()
        user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
        user.investment_amount = amount
        db.add(user)
        db.commit()
        db.close()
        await message.answer(f"✅ تم تحديث مبلغ الاستثمار إلى {amount} USDT.")
        await message.answer("العودة للقائمة الرئيسية:", reply_markup=main_menu_keyboard())
        await state.finish()
    except Exception:
        await message.answer("❌ أدخل رقم صحيح للمبلغ.")

# 2- بدء استثمار حقيقي
@dp.callback_query_handler(lambda c: c.data == "menu_start_invest")
async def start_invest_handler(call: types.CallbackQuery):
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=call.from_user.id).first()

    if not user or (not user.binance_active and not user.kucoin_active):
        await call.answer("❌ لم تقم بربط أي منصة تداول.")
        db.close()
        return
    if user.investment_amount <= 0:
        await call.answer("❌ لم تحدد مبلغ الاستثمار، الرجاء تحديده أولاً.")
        db.close()
        return

    user.investment_status = "started"
    db.add(user)
    db.commit()
    db.close()
    await call.answer()
    await call.message.edit_text("🚀 تم بدء الاستثمار والمراجحة تلقائياً. يمكنك إيقافه من القائمة متى شئت.")
    asyncio.create_task(run_arbitrage_loop(call.from_user.id))

# 3- استثمار وهمي
@dp.callback_query_handler(lambda c: c.data == "menu_fake_invest")
async def fake_invest_handler(call: types.CallbackQuery):
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=call.from_user.id).first()
    db.close()
    if not user or (not user.binance_active and not user.kucoin_active):
        await call.answer("❌ لم تقم بربط أي منصة تداول.")
        return
    if user.investment_amount <= 0:
        await call.answer("❌ لم تحدد مبلغ الاستثمار، الرجاء تحديده أولاً.")
        return

    await call.answer()
    # تنفيذ وهمي: استخدام بيانات السوق الحقيقية فقط بدون تنفيذ أوامر
    await call.message.edit_text("🛑 بدء استثمار وهمي... سيتم إرسال تحديثات دورية بناءً على أسعار السوق الحقيقية دون استخدام أموال فعلية.")
    asyncio.create_task(run_fake_invest_loop(call.from_user.id))

# 4- كشف حساب عن فترة
@dp.callback_query_handler(lambda c: c.data == "menu_report")
async def report_start_handler(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.edit_text("📅 أرسل تاريخ بداية الفترة (مثلاً: 2023-08-01):")
    await Form.waiting_report_start.set()

@dp.message_handler(state=Form.waiting_report_start)
async def report_start_date_received(message: types.Message, state: FSMContext):
    try:
        start_date = datetime.strptime(message.text.strip(), "%Y-%m-%d")
        await state.update_data(report_start=start_date)
        await message.answer("📅 أرسل تاريخ نهاية الفترة (مثلاً: 2023-08-10):")
        await Form.waiting_report_end.set()
    except Exception:
        await message.answer("❌ تنسيق التاريخ غير صحيح. استخدم: YYYY-MM-DD")

@dp.message_handler(state=Form.waiting_report_end)
async def report_end_date_received(message: types.Message, state: FSMContext):
    try:
        end_date = datetime.strptime(message.text.strip(), "%Y-%m-%d")
        data = await state.get_data()
        start_date = data["report_start"]

        if end_date < start_date:
            await message.answer("❌ تاريخ النهاية لا يمكن أن يكون قبل البداية.")
            return

        db = SessionLocal()
        user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
        trades = db.query(TradeLog).filter(
            TradeLog.user_id == user.id,
            TradeLog.timestamp >= start_date,
            TradeLog.timestamp <= end_date + timedelta(days=1),
        ).all()
        db.close()

        if not trades:
            await message.answer("لا توجد بيانات عن هذه الفترة.")
            await state.finish()
            return

        report_text = f"📊 كشف حساب من {start_date.date()} إلى {end_date.date()}:\n"
        total_profit = 0
        for t in trades:
            report_text += f"{t.timestamp.date()} - {t.trade_type} - ربح: {t.profit:.2f} USDT\n"
            total_profit += t.profit
        report_text += f"\n💰 إجمالي الربح: {total_profit:.2f} USDT"
        await message.answer(report_text)
        await state.finish()
    except Exception:
        await message.answer("❌ تنسيق التاريخ غير صحيح. استخدم: YYYY-MM-DD")

# 5- حالة السوق (استخدام OpenAI لتحليل السوق)

import openai

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

@dp.callback_query_handler(lambda c: c.data == "menu_market_status")
async def market_status_handler(call: types.CallbackQuery):
    await call.answer()
    if not OPENAI_API_KEY:
        await call.message.edit_text("❌ لا يوجد مفتاح OpenAI API مفعل. لا يمكن عرض حالة السوق.", reply_markup=main_menu_keyboard())
        return

    # طلب من OpenAI تحليل السوق مع تعليمات بالعربية
    prompt = (
        "أنت خبير في أسواق العملات الرقمية. اعطني تحليل موجز لحالة سوق العملات الرقمية الحالية، "
        "توقعات الأسعار، ونصائح للمستثمرين معتمد على أحدث المؤشرات والتقارير."
    )
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.7,
        )
        analysis = response.choices[0].message.content
        text = f"📈 تحليل حالة السوق:\n{analysis}"
        await call.message.edit_text(text, reply_markup=main_menu_keyboard())
    except Exception as e:
        await call.message.edit_text(f"❌ خطأ في جلب تحليل السوق: {e}", reply_markup=main_menu_keyboard())

# 6- إيقاف الاستثمار
@dp.callback_query_handler(lambda c: c.data == "menu_stop_invest")
async def stop_invest_handler(call: types.CallbackQuery):
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=call.from_user.id).first()
    if not user:
        await call.answer("❌ لم يتم ربط حسابك.")
        db.close()
        return
    user.investment_status = "stopped"
    db.add(user)
    db.commit()
    db.close()
    await call.answer()
    await call.message.edit_text("⏹️ تم إيقاف الاستثمار. لن يتم استخدام أموالك حتى تطلب البدء مجدداً.", reply_markup=main_menu_keyboard())

# 7- ارشاد العميل كيف يحصل على مفاتيح API
@dp.callback_query_handler(lambda c: c.data == "menu_api_help")
async def api_help_handler(call: types.CallbackQuery):
    await call.answer()
    help_text = (
        "🔑 للحصول على مفاتيح API:\n\n"
        "Binance:\n"
        "- سجل دخول إلى حسابك.\n"
        "- اذهب إلى API Management.\n"
        "- أنشئ مفتاح API جديد مع تفعيل صلاحيات (Spot Trading) فقط.\n"
        "- لا تفعل صلاحيات السحب.\n\n"
        "KuCoin:\n"
        "- سجل دخول إلى حسابك.\n"
        "- اذهب إلى API Management.\n"
        "- أنشئ API جديد مع تفعيل صلاحيات (General, Spot Trading) فقط.\n"
        "- فعّل الـ Passphrase واحفظه.\n"
        "- لا تفعل صلاحيات السحب.\n\n"
        "🛑 تأكد من تفعيل الصلاحيات الضرورية فقط لتجنب مشاكل الربط."
    )
    await call.message.edit_text(help_text, reply_markup=main_menu_keyboard())

# ----------------------- LOOP FUNCTIONS -----------------------

async def run_arbitrage_loop(telegram_id: int):
    """تشغيل المراجحة الحقيقية بناء على مفاتيح المستخدم وحالته"""
    while True:
        await asyncio.sleep(10)  # تأخير بين كل عملية مراجحة
        db = SessionLocal()
        user = db.query(User).filter_by(telegram_id=telegram_id).first()
        if not user or user.investment_status != "started":
            db.close()
            break  # إيقاف الحلقة لو تم إيقاف الاستثمار

        # مثال مبسط: استدعاء APIs ومنطق المراجحة
        # ... هنا تضع خوارزمية المراجحة الحقيقية ...

        # مثال: حفظ صفقة وهمية في السجل (تعديل حسب الواقع)
        trade = TradeLog(
            user_id=user.id,
            trade_type="arbitrage_real",
            amount=user.investment_amount * 0.01,
            price=100,
            profit=1.0,
            timestamp=datetime.utcnow(),
        )
        db.add(trade)
        db.commit()
        db.close()

@dp.message_handler(commands=["stop"])
async def stop_command_handler(message: types.Message):
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
    if user:
        user.investment_status = "stopped"
        db.add(user)
        db.commit()
    db.close()
    await message.answer("⏹️ تم إيقاف الاستثمار.")

async def run_fake_invest_loop(telegram_id: int):
    """تشغيل استثمار وهمي باستخدام بيانات حقيقية فقط، بدون تنفيذ أوامر حقيقية"""
    while True:
        await asyncio.sleep(15)
        db = SessionLocal()
        user = db.query(User).filter_by(telegram_id=telegram_id).first()
        if not user or user.investment_status == "started":
            db.close()
            break  # إيقاف الحلقة لو بدأ استثمار حقيقي أو أوقف المستخدم الاستثمار

        # جلب بيانات السوق من APIs (مثلاً أسعار Binance/KuCoin)
        # ثم إرسال تحديثات للمستخدم بشكل وهمي
        # مثال إرسال رسالة (يمكن تحسينه لاحقاً)
        await bot.send_message(telegram_id, "📊 تحديث وهمي لحالة السوق بناء على الأسعار الحقيقية.")

        db.close()

# ----------------------- START BOT -----------------------

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
