import os
import asyncio
import logging
from datetime import datetime, timedelta

import requests

from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker

from binance.client import Client as BinanceClient
from kucoin.client import Market, Trade

import openai

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not BOT_TOKEN or not DATABASE_URL or not OPENAI_API_KEY:
    raise Exception("❌ Missing environment variables BOT_TOKEN, DATABASE_URL or OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

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

    # Binance
    binance_api = Column(String(256), nullable=True)
    binance_secret = Column(String(256), nullable=True)
    binance_active = Column(Boolean, default=False)

    # KuCoin
    kucoin_api = Column(String(256), nullable=True)
    kucoin_secret = Column(String(256), nullable=True)
    kucoin_passphrase = Column(String(256), nullable=True)
    kucoin_active = Column(Boolean, default=False)

    # Bybit
    bybit_api = Column(String(256), nullable=True)
    bybit_secret = Column(String(256), nullable=True)
    bybit_active = Column(Boolean, default=False)

    # OKX
    okx_api = Column(String(256), nullable=True)
    okx_secret = Column(String(256), nullable=True)
    okx_passphrase = Column(String(256), nullable=True)
    okx_active = Column(Boolean, default=False)

    # Kraken
    kraken_api = Column(String(256), nullable=True)
    kraken_secret = Column(String(256), nullable=True)
    kraken_active = Column(Boolean, default=False)

    # Coinbase Exchange (Coinbase Pro سابقاً)
    coinbase_api = Column(String(256), nullable=True)
    coinbase_secret = Column(String(256), nullable=True)
    coinbase_passphrase = Column(String(256), nullable=True)
    coinbase_active = Column(Boolean, default=False)

    # Investment
    investment_amount = Column(Float, default=0.0)
    investment_status = Column(String(20), default="stopped")


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

# ----------------------- FSM STATES -----------------------

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

SUPPORTED_PLATFORMS = [
    ("binance", "Binance", False),          # needs passphrase? False
    ("kucoin", "KuCoin", True),
    ("bybit", "Bybit", False),
    ("okx", "OKX", True),
    ("kraken", "Kraken", False),
    ("coinbase", "Coinbase Exchange", True),  # API/Secret/Passphrase
]

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

# ---------- Verify Keys (return tuple: (bool, message)) ----------

async def verify_binance_keys(api_key, secret_key):
    try:
        client = BinanceClient(api_key, secret_key)
        client.get_account()
        return True, "✅ مفاتيح Binance صالحة."
    except Exception as e:
        return False, f"❌ Binance: {e}"

async def verify_kucoin_keys(api_key, secret_key, passphrase):
    try:
        trade_client = Trade(api_key, secret_key, passphrase)
        accounts = trade_client.get_accounts()
        return (bool(accounts), "✅ مفاتيح KuCoin صالحة." if accounts else "❌ KuCoin: لا توجد حسابات.")
    except Exception as e:
        return False, f"❌ KuCoin: {e}"

async def verify_bybit_keys(api_key, secret_key):
    """
    يتطلب مكتبة pybit: pip install pybit
    """
    try:
        from pybit.unified_trading import HTTP
        session = HTTP(api_key=api_key, api_secret=secret_key)
        resp = session.get_wallet_balance(accountType="UNIFIED")
        ok = isinstance(resp, dict) and resp.get("retCode") == 0
        return (ok, "✅ مفاتيح Bybit صالحة." if ok else f"❌ Bybit: {resp}")
    except ImportError:
        return False, "❌ Bybit: رجاءً ثبّت pybit (pip install pybit)."
    except Exception as e:
        return False, f"❌ Bybit: {e}"

async def verify_okx_keys(api_key, secret_key, passphrase):
    """
    يتطلب مكتبة okx-api: pip install okx
    """
    try:
        import okx.Account as Account
        flag = "0"  # 0: real, 1: demo
        accountAPI = Account.AccountAPI(api_key, secret_key, passphrase, False, flag)
        resp = accountAPI.get_account_balance()
        ok = isinstance(resp, dict) and resp.get("code") in ("0", 0)
        return (ok, "✅ مفاتيح OKX صالحة." if ok else f"❌ OKX: {resp}")
    except ImportError:
        return False, "❌ OKX: رجاءً ثبّت okx (pip install okx)."
    except Exception as e:
        return False, f"❌ OKX: {e}"

async def verify_kraken_keys(api_key, secret_key):
    """
    يتطلب مكتبة krakenex: pip install krakenex
    """
    try:
        import krakenex
        k = krakenex.API(key=api_key, secret=secret_key)
        resp = k.query_private('Balance')
        ok = isinstance(resp, dict) and resp.get("error") == []
        return (ok, "✅ مفاتيح Kraken صالحة." if ok else f"❌ Kraken: {resp}")
    except ImportError:
        return False, "❌ Kraken: رجاءً ثبّت krakenex (pip install krakenex)."
    except Exception as e:
        return False, f"❌ Kraken: {e}"

async def verify_coinbase_keys(api_key, secret_key, passphrase):
    """
    Coinbase Exchange (Pro سابقاً). يتطلب cbpro أو الخاص بـ Advanced Trade.
    نستخدم cbpro كحل سريع: pip install cbpro
    """
    try:
        import cbpro
        auth_client = cbpro.AuthenticatedClient(api_key, secret_key, passphrase)
        accounts = list(auth_client.get_accounts())
        ok = len(accounts) > 0 and isinstance(accounts[0], dict)
        return (ok, "✅ مفاتيح Coinbase صالحة." if ok else "❌ Coinbase: لم يتم استرجاع الحسابات.")
    except ImportError:
        return False, "❌ Coinbase: رجاءً ثبّت cbpro (pip install cbpro)."
    except Exception as e:
        return False, f"❌ Coinbase: {e}"

# ---------- UI Helpers ----------

def platform_status_text(name: str, is_active: bool, is_linked: bool):
    return (("✅ " if is_active else "❌ ") + name + (" (مربوط)" if is_linked else " (غير مربوط)"))

def user_platforms_keyboard(user: User):
    kb = InlineKeyboardMarkup(row_width=2)

    items = [
        ("platform_binance", platform_status_text("Binance", user.binance_active, bool(user.binance_api))),
        ("platform_kucoin", platform_status_text("KuCoin", user.kucoin_active, bool(user.kucoin_api))),
        ("platform_bybit", platform_status_text("Bybit", user.bybit_active, bool(user.bybit_api))),
        ("platform_okx", platform_status_text("OKX", user.okx_active, bool(user.okx_api))),
        ("platform_kraken", platform_status_text("Kraken", user.kraken_active, bool(user.kraken_api))),
        ("platform_coinbase", platform_status_text("Coinbase", user.coinbase_active, bool(user.coinbase_api))),
    ]
    for cb, text in items:
        kb.insert(InlineKeyboardButton(text, callback_data=cb))

    kb.add(InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu"))
    return kb

def main_menu_keyboard():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("1️⃣ تسجيل/تعديل بيانات التداول", callback_data="menu_edit_trading_data"),
        InlineKeyboardButton("2️⃣ ابدأ استثمار", callback_data="menu_start_invest"),
        InlineKeyboardButton("3️⃣ ضبط مبلغ الاستثمار", callback_data="menu_set_amount"),
        InlineKeyboardButton("4️⃣ كشف حساب عن فترة", callback_data="menu_report"),
        InlineKeyboardButton("5️⃣ حالة السوق", callback_data="menu_market_status"),
        InlineKeyboardButton("6️⃣ إيقاف الاستثمار", callback_data="menu_stop_invest"),
        InlineKeyboardButton("⚙️ اختبار مفاتيح KuCoin", callback_data="test_kucoin_prompt"),
    )
    return kb

def count_active_exchanges(user: User) -> int:
    flags = [
        user.binance_active,
        user.kucoin_active,
        user.bybit_active,
        user.okx_active,
        user.kraken_active,
        user.coinbase_active,
    ]
    return sum(1 for f in flags if f)

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

    # Determine which fields are needed
    needs_passphrase = platform in ("kucoin", "okx", "coinbase")
    await call.message.edit_text(f"أرسل مفتاح API الخاص بمنصة {platform.capitalize()}:")
    await Form.waiting_api_key.set()
    await state.update_data(needs_passphrase=needs_passphrase)

@dp.message_handler(state=Form.waiting_api_key)
async def api_key_received(message: types.Message, state: FSMContext):
    data = await state.get_data()
    platform = data["selected_platform"]
    api_key = message.text.strip()
    await state.update_data(api_key=api_key)

    await message.answer(f"أرسل الـ Secret Key الخاص بـ {platform.capitalize()}:")
    await Form.waiting_secret_key.set()

@dp.message_handler(state=Form.waiting_secret_key)
async def secret_key_received(message: types.Message, state: FSMContext):
    data = await state.get_data()
    platform = data["selected_platform"]
    secret_key = message.text.strip()
    await state.update_data(secret_key=secret_key)

    if data.get("needs_passphrase", False):
        await message.answer(f"أرسل الـ Passphrase الخاص بـ {platform.capitalize()}:")
        await Form.waiting_passphrase.set()
    else:
        # verify now
        await handle_platform_save(message, state, passphrase=None)

@dp.message_handler(state=Form.waiting_passphrase)
async def passphrase_received(message: types.Message, state: FSMContext):
    passphrase = message.text.strip()
    await handle_platform_save(message, state, passphrase=passphrase)

async def handle_platform_save(message: types.Message, state: FSMContext, passphrase: str = None):
    data = await state.get_data()
    platform = data["selected_platform"]
    api_key = data["api_key"]
    secret_key = data["secret_key"]

    # Verify per platform
    valid = False
    msg = ""
    if platform == "binance":
        valid, msg = await verify_binance_keys(api_key, secret_key)
    elif platform == "kucoin":
        valid, msg = await verify_kucoin_keys(api_key, secret_key, passphrase or "")
    elif platform == "bybit":
        valid, msg = await verify_bybit_keys(api_key, secret_key)
    elif platform == "okx":
        valid, msg = await verify_okx_keys(api_key, secret_key, passphrase or "")
    elif platform == "kraken":
        valid, msg = await verify_kraken_keys(api_key, secret_key)
    elif platform == "coinbase":
        valid, msg = await verify_coinbase_keys(api_key, secret_key, passphrase or "")

    if not valid:
        await message.answer(f"{msg}\n\n❌ المفاتيح غير صحيحة أو لا تحتوي على الصلاحيات اللازمة.\nتأكد من تفعيل صلاحيات القراءة والتداول فقط، وأعد المحاولة.")
        await state.finish()
        return

    # Save to DB
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=message.from_user.id).first()

    if platform == "binance":
        user.binance_api = api_key
        user.binance_secret = secret_key
        user.binance_active = True
    elif platform == "kucoin":
        user.kucoin_api = api_key
        user.kucoin_secret = secret_key
        user.kucoin_passphrase = passphrase
        user.kucoin_active = True
    elif platform == "bybit":
        user.bybit_api = api_key
        user.bybit_secret = secret_key
        user.bybit_active = True
    elif platform == "okx":
        user.okx_api = api_key
        user.okx_secret = secret_key
        user.okx_passphrase = passphrase
        user.okx_active = True
    elif platform == "kraken":
        user.kraken_api = api_key
        user.kraken_secret = secret_key
        user.kraken_active = True
    elif platform == "coinbase":
        user.coinbase_api = api_key
        user.coinbase_secret = secret_key
        user.coinbase_passphrase = passphrase
        user.coinbase_active = True

    db.add(user)
    db.commit()
    db.close()

    await message.answer(f"{msg}\n\n✅ تم ربط {platform.capitalize()} بنجاح!")
    await state.finish()
    await message.answer("العودة للقائمة الرئيسية:", reply_markup=main_menu_keyboard())

# --------- ضبط مبلغ الاستثمار ---------

@dp.callback_query_handler(lambda c: c.data == "menu_set_amount")
async def set_amount_handler(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.edit_text("💵 أرسل مبلغ الاستثمار بالـ USDT (مثال: 100):")
    await Form.waiting_investment_amount.set()

@dp.message_handler(state=Form.waiting_investment_amount)
async def set_amount_value(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.strip())
        if amount <= 0:
            raise ValueError()
        db = SessionLocal()
        user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
        user.investment_amount = amount
        db.add(user)
        db.commit()
        db.close()
        await state.finish()
        await message.answer(f"✅ تم ضبط مبلغ الاستثمار: {amount:.2f} USDT", reply_markup=main_menu_keyboard())
    except Exception:
        await message.answer("❌ قيمة غير صحيحة. أرسل رقمًا أكبر من 0.")

# --------- التقارير ---------

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

# --------- حالة السوق مع OpenAI ---------

async def get_market_analysis():
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful crypto market analyst."},
                {"role": "user", "content": (
                    "اعطني ملخص تحليل سوق العملات الرقمية الحالي، مع أسعار بعض العملات الرئيسية مثل BTC و ETH،"
                    " ونبذة عن توقعات السوق بناء على مؤشرات تقنية مثل RSI و MACD."
                    " اذكر التحذيرات إن وجدت."
                )}
            ],
            max_tokens=300,
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ خطأ في جلب تحليل السوق من OpenAI: {str(e)}"

@dp.callback_query_handler(lambda c: c.data == "menu_market_status")
async def market_status_handler(call: types.CallbackQuery):
    await call.answer()
    analysis_text = await get_market_analysis()
    await call.message.edit_text(analysis_text, reply_markup=main_menu_keyboard())

# --------- اختبار مفاتيح KuCoin ---------

async def test_kucoin_api_keys(api_key, secret_key, passphrase):
    try:
        trade_client = Trade(api_key, secret_key, passphrase)
        accounts = trade_client.get_accounts()
        if accounts:
            return "✅ مفاتيح KuCoin صالحة وتم التحقق منها."
        else:
            return "❌ المفتاح صالح لكن لا توجد حسابات مرتبطة."
    except Exception as e:
        return f"❌ خطأ في التحقق من مفاتيح KuCoin: {str(e)}"

@dp.callback_query_handler(lambda c: c.data == "test_kucoin_prompt")
async def test_kucoin_prompt_handler(call: types.CallbackQuery):
    await call.answer()
    await call.message.edit_text(
        "أرسل المفاتيح لاختبارها بهذه الصيغة:\n\n"
        "/test_kucoin API_KEY SECRET_KEY PASSPHRASE\n\n"
        "مثال:\n/test_kucoin abc123 def456 ghi789"
    )

@dp.message_handler(commands=["test_kucoin"])
async def test_kucoin_handler(message: types.Message):
    parts = message.text.split()
    if len(parts) != 4:
        await message.answer("❌ الصيغة: /test_kucoin <API_KEY> <SECRET_KEY> <PASSPHRASE>")
        return
    api_key, secret_key, passphrase = parts[1], parts[2], parts[3]
    result = await test_kucoin_api_keys(api_key, secret_key, passphrase)
    await message.answer(result)

# --------- مساعدات الأسعار العامة (بدون مفاتيح) ---------

def fetch_public_price(exchange: str) -> float:
    """
    إحضار سعر BTC/USDT من واجهات عامة لكل منصة.
    Coinbase تستخدم USD غالباً لذا غير مدعومة هنا في التسعير.
    """
    try:
        if exchange == "binance":
            r = requests.get("https://api.binance.com/api/v3/ticker/price", params={"symbol": "BTCUSDT"}, timeout=5)
            return float(r.json()["price"])
        if exchange == "kucoin":
            r = requests.get("https://api.kucoin.com/api/v1/market/orderbook/level1", params={"symbol": "BTC-USDT"}, timeout=5)
            return float(r.json()["data"]["price"])
        if exchange == "bybit":
            r = requests.get("https://api.bybit.com/v5/market/tickers", params={"category": "spot", "symbol": "BTCUSDT"}, timeout=5)
            data = r.json()
            return float(data["result"]["list"][0]["lastPrice"])
        if exchange == "okx":
            r = requests.get("https://www.okx.com/api/v5/market/ticker", params={"instId": "BTC-USDT"}, timeout=5)
            return float(r.json()["data"][0]["last"])
        if exchange == "kraken":
            # Kraken يستخدم XBTUSDT
            r = requests.get("https://api.kraken.com/0/public/Ticker", params={"pair": "XBTUSDT"}, timeout=5)
            data = r.json()["result"]
            first_key = list(data.keys())[0]
            return float(data[first_key]["c"][0])
        # Coinbase: BTC-USD (غير مُدرج في مقارنة USDT هنا)
        return None
    except Exception:
        return None

def get_user_active_exchanges(user: User):
    actives = []
    if user.binance_active: actives.append("binance")
    if user.kucoin_active: actives.append("kucoin")
    if user.bybit_active: actives.append("bybit")
    if user.okx_active: actives.append("okx")
    if user.kraken_active: actives.append("kraken")
    # Coinbase مستبعدة من التسعير USDT
    return actives

# ----------------------- START/STOP INVEST -----------------------

@dp.callback_query_handler(lambda c: c.data == "menu_start_invest")
async def start_invest_handler(call: types.CallbackQuery):
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=call.from_user.id).first()

    if not user:
        await call.answer("❌ لا يوجد مستخدم.")
        db.close()
        return

    if count_active_exchanges(user) < 2:
        await call.answer("❌ لازم تربط منصتين على الأقل قبل بدء الاستثمار.")
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

@dp.callback_query_handler(lambda c: c.data == "menu_stop_invest")
async def stop_invest_handler(call: types.CallbackQuery):
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=call.from_user.id).first()
    if user:
        user.investment_status = "stopped"
        db.add(user)
        db.commit()
    db.close()
    await call.answer("🛑 تم إيقاف الاستثمار.")

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
            active_exchs = get_user_active_exchanges(user)
            if len(active_exchs) < 2:
                await bot.send_message(user.telegram_id, "❌ يجب أن تبقى منصتان على الأقل مفعّلتين.")
                user.investment_status = "stopped"
                db.add(user)
                db.commit()
                db.close()
                return

            # احصل على الأسعار من كل منصة فعّالة
            prices = {}
            for ex in active_exchs:
                p = fetch_public_price(ex)
                if p:
                    prices[ex] = p

            if len(prices) < 2:
                await bot.send_message(user.telegram_id, "لا توجد بيانات أسعار كافية حالياً.")
                await asyncio.sleep(60)
                continue

            # ابحث عن أفضل فرق سعري
            # buy_on بأقل سعر، sell_on بأعلى سعر
            buy_on = min(prices, key=prices.get)
            sell_on = max(prices, key=prices.get)
            buy_price = prices[buy_on]
            sell_price = prices[sell_on]

            threshold = 20.0  # USDT
            min_price = min(buy_price, sell_price)
            amount_to_trade = user.investment_amount / min_price if min_price else 0

            executed = False
            profit = 0.0
            trade_type = None

            if sell_price - buy_price >= threshold and amount_to_trade > 0:
                # تنفيذ فعلي فقط إن كانت المنصتان Binance و KuCoin (كمرحلة أولى)
                if (buy_on == "binance" and sell_on == "kucoin") or (buy_on == "kucoin" and sell_on == "binance"):
                    binance_client = create_binance_client(user)
                    kucoin_market, kucoin_trade = create_kucoin_clients(user)

                    if buy_on == "binance" and binance_client and kucoin_trade:
                        # Buy on Binance, Sell on KuCoin
                        binance_client.order_market_buy(symbol="BTCUSDT", quantity=amount_to_trade)
                        kucoin_trade.create_market_order('BTC-USDT', 'sell', size=str(amount_to_trade))
                        profit = (sell_price - buy_price) * amount_to_trade
                        trade_type = "Buy Binance / Sell KuCoin"
                        executed = True

                    elif buy_on == "kucoin" and kucoin_trade and binance_client:
                        kucoin_trade.create_market_order('BTC-USDT', 'buy', size=str(amount_to_trade))
                        binance_client.order_market_sell(symbol="BTCUSDT", quantity=amount_to_trade)
                        profit = (sell_price - buy_price) * amount_to_trade
                        trade_type = "Buy KuCoin / Sell Binance"
                        executed = True
                else:
                    # منصات أخرى: إظهار فرصة فقط (بدون تنفيذ)
                    await bot.send_message(
                        user.telegram_id,
                        f"💡 فرصة مراجحة: اشترِ على {buy_on.upper()} بسعر {buy_price:.2f} وبِع على {sell_on.upper()} بسعر {sell_price:.2f}."
                        " (التنفيذ التلقائي لهذه المنصات سيُضاف لاحقاً)"
                    )

            if executed and trade_type:
                trade_log = TradeLog(
                    user_id=user.id,
                    trade_type=trade_type,
                    amount=amount_to_trade,
                    price=min_price,
                    profit=profit,
                )
                db.add(trade_log)
                await bot.send_message(user.telegram_id, f"✅ تمت صفقة {trade_type} وربح: {profit:.2f} USDT")
                db.commit()
            else:
                if not executed:
                    await bot.send_message(user.telegram_id, "لا توجد فرصة مراجحة مناسبة حالياً.")

        except Exception as e:
            await bot.send_message(user.telegram_id, f"❌ خطأ في المراجحة: {str(e)}")

        await asyncio.sleep(60)

# ----------------------- RUN BOT -----------------------

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
