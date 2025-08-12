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
        market_client = Market()
        trade_client = Trade(user.kucoin_api, user.kucoin_secret, user.kucoin_passphrase)
        return market_client, trade_client
    return None, None

async def verify_binance_keys(api_key, secret_key):
    try:
        client = BinanceClient(api_key, secret_key)
        client.get_account()
        return True, ""
    except Exception as e:
        return False, f"خطأ في التحقق من مفاتيح Binance: {str(e)}"

async def verify_kucoin_keys(api_key, secret_key, passphrase):
    try:
        trade_client = Trade(api_key, secret_key, passphrase)
        trade_client.get_account()
        return True, ""
    except Exception as e:
        return False, f"خطأ في التحقق من مفاتيح KuCoin: {str(e)}"

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
    )
    return kb

def get_binance_balance(client: BinanceClient, asset: str = "USDT"):
    try:
        account = client.get_account()
        for bal in account['balances']:
            if bal['asset'] == asset:
                return float(bal['free'])
        return 0.0
    except Exception:
        return 0.0

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
        valid, error_msg = await verify_binance_keys(data["api_key"], secret_key)
        if not valid:
            await message.answer(f"❌ المفاتيح غير صحيحة أو لا تحتوي على الصلاحيات اللازمة.\n{error_msg}\nتأكد من تفعيل صلاحيات القراءة والتداول فقط، وأعد المحاولة.")
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

    valid, error_msg = await verify_kucoin_keys(data["api_key"], data["secret_key"], passphrase)
    if not valid:
        await message.answer(f"❌ المفاتيح غير صحيحة أو لا تحتوي على الصلاحيات اللازمة.\n{error_msg}\nتأكد من تفعيل صلاحيات القراءة والتداول فقط، وأعد المحاولة.")
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

# 3- استثمار وهمي (يستخدم بيانات Binance الحقيقية بدون تنفيذ أوامر)
@dp.callback_query_handler(lambda c: c.data == "menu_fake_invest")
async def fake_invest_handler(call: types.CallbackQuery):
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=call.from_user.id).first()

    if not user or not user.binance_active:
        await call.answer("❌ لم تقم بربط منصة Binance للاستثمار الوهمي.")
        db.close()
        return

    binance_client = create_binance_client(user)
    if not binance_client:
        await call.answer("❌ لم يتم تهيئة عميل Binance بشكل صحيح.")
        db.close()
        return

    balance = get_binance_balance(binance_client, "USDT")
    price = float(binance_client.get_symbol_ticker(symbol="BTCUSDT")['price'])

    amount_to_trade = balance / price if price else 0

    kucoin_market, _ = create_kucoin_clients(user)
    kucoin_price = None
    if kucoin_market:
        kucoin_price = float(kucoin_market.get_ticker("BTC-USDT")['price'])

    threshold = 20.0
    trade_opportunity = None
    profit_estimate = 0

    if kucoin_price:
        if price + threshold < kucoin_price:
            trade_opportunity = "شراء من Binance وبيع في KuCoin (وهمي)"
            profit_estimate = (kucoin_price - price) * amount_to_trade
        elif kucoin_price + threshold < price:
            trade_opportunity = "شراء من KuCoin وبيع في Binance (وهمي)"
            profit_estimate = (price - kucoin_price) * amount_to_trade

    report = f"رصيدك الحالي في Binance: {balance:.2f} USDT\nسعر BTC حالياً في Binance: {price:.2f} USDT"

    if trade_opportunity:
        report += f"\n⚠️ فرصة مراجحة وهمية:\n{trade_opportunity}\nالكمية: {amount_to_trade:.6f} BTC\nالربح المتوقع: {profit_estimate:.2f} USDT"
    else:
        report += "\n⚠️ لا توجد فرص مراجحة وهمية حالياً."

    await call.answer()
    await call.message.edit_text(report, reply_markup=main_menu_keyboard())
    db.close()

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

# 5- حالة السوق (تحليل مبسط - يمكن تطويره باستخدام OpenAI لاحقاً)
@dp.callback_query_handler(lambda c: c.data == "menu_market_status")
async def market_status_handler(call: types.CallbackQuery):
    await call.answer()
    # مثال: تحليل مبسط — يمكنك إضافة ذكاء أكثر لاحقاً
    text = "📈 حالة السوق الحالية:\n- السوق مستقر نسبياً.\n- نصيحتي: ابدأ استثمارك إذا كنت مستعداً للمخاطرة."
    await call.message.edit_text(text, reply_markup=main_menu_keyboard())

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

# ----------------------- ARBITRAGE LOOP -----------------------

async def run_arbitrage_loop(user_telegram_id):
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=user_telegram_id).first()
    if not user or user.investment_status != "started":
        db.close()
        return

    while True:
        db.refresh(user)
        if user.investment_status != "started":
            db.close()
            return

        try:
            binance_client = create_binance_client(user)
            kucoin_market, kucoin_trade = create_kucoin_clients(user)

            if not binance_client and not kucoin_trade:
                await bot.send_message(user.telegram_id, "❌ لا توجد منصات مفعلة للاستثمار.")
                user.investment_status = "stopped"
                db.add(user)
                db.commit()
                db.close()
                return

            binance_price = None
            kucoin_price = None

            if binance_client:
                binance_price = float(binance_client.get_symbol_ticker(symbol="BTCUSDT")['price'])
            if kucoin_market:
                kucoin_price = float(kucoin_market.get_ticker("BTC-USDT")['price'])

            threshold = 20.0
            amount_to_invest = user.investment_amount

            # المراجحة بين بينانس و KuCoin
            if binance_price and kucoin_price and amount_to_invest > 0:
                if binance_price + threshold < kucoin_price:
                    # شراء من بينانس وبيع في KuCoin
                    # تنفيذ الأوامر هنا حسب المنصة (لم يتم إضافة التنفيذ هنا)
                    profit = (kucoin_price - binance_price) * (amount_to_invest / binance_price)
                    await bot.send_message(user.telegram_id,
                        f"✅ فرصة مراجحة حقيقية: شراء من Binance بسعر {binance_price} وبيع في KuCoin بسعر {kucoin_price}.\nالربح المتوقع: {profit:.2f} USDT"
                    )
                elif kucoin_price + threshold < binance_price:
                    profit = (binance_price - kucoin_price) * (amount_to_invest / kucoin_price)
                    await bot.send_message(user.telegram_id,
                        f"✅ فرصة مراجحة حقيقية: شراء من KuCoin بسعر {kucoin_price} وبيع في Binance بسعر {binance_price}.\nالربح المتوقع: {profit:.2f} USDT"
                    )

            await asyncio.sleep(60)  # انتظار دقيقة قبل فحص جديد
        except Exception as e:
            logging.error(f"Error in arbitrage loop for user {user_telegram_id}: {e}")
            await bot.send_message(user.telegram_id, f"❌ حدث خطأ أثناء تنفيذ المراجحة: {e}")
            await asyncio.sleep(60)

# ----------------------- RUN BOT -----------------------

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
