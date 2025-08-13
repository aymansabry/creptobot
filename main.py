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

# SDKs المنصات
from binance.client import Client as BinanceClient
from kucoin.client import Market as KucoinMarket, Trade as KucoinTrade
# Bybit / OKX / Kraken سنستورد داخل الدوال لتفادي كسر التشغيل إن لم تكن الحزم مثبتة

import openai

logging.basicConfig(level=logging.INFO)

# ----------------------- ENV -----------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not BOT_TOKEN or not DATABASE_URL or not OPENAI_API_KEY:
    raise Exception("❌ Missing environment variables BOT_TOKEN, DATABASE_URL or OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

# ----------------------- BOT/DB -----------------------
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# ----------------------- MODELS -----------------------
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

    # Coinbase (عرض فقط الآن)
    coinbase_api = Column(String(256), nullable=True)
    coinbase_secret = Column(String(256), nullable=True)
    coinbase_passphrase = Column(String(256), nullable=True)
    coinbase_active = Column(Boolean, default=False)

    investment_amount = Column(Float, default=0.0)
    investment_status = Column(String(20), default="stopped")


class TradeLog(Base):
    __tablename__ = "trade_logs"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    trade_type = Column(String(80))
    amount = Column(Float)
    price = Column(Float)
    profit = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(engine)

# ----------------------- FSM -----------------------
class Form(StatesGroup):
    platform_choice = State()
    waiting_api_key = State()
    waiting_secret_key = State()
    waiting_passphrase = State()
    waiting_investment_amount = State()
    waiting_report_start = State()
    waiting_report_end = State()

# ----------------------- PLATFORM HELPERS -----------------------
def count_active_exchanges(user: User) -> int:
    flags = [
        user.binance_active,
        user.kucoin_active,
        user.bybit_active,
        user.okx_active,
        user.kraken_active,
        # coinbase_active مستبعدة للتنفيذ حالياً
    ]
    return sum(1 for f in flags if f)

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
        ("platform_coinbase", platform_status_text("Coinbase (عرض فقط)", user.coinbase_active, bool(user.coinbase_api))),
    ]
    for cb, text in items:
        kb.insert(InlineKeyboardButton(text, callback_data=cb))
    kb.add(InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu"))
    return kb

def main_menu_keyboard():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("1️⃣ تسجيل/تعديل بيانات التداول", callback_data="menu_edit_trading_data"),
        InlineKeyboardButton("2️⃣ ضبط مبلغ الاستثمار", callback_data="menu_set_amount"),
        InlineKeyboardButton("3️⃣ ابدأ استثمار", callback_data="menu_start_invest"),
        InlineKeyboardButton("4️⃣ إيقاف الاستثمار", callback_data="menu_stop_invest"),
        InlineKeyboardButton("5️⃣ كشف حساب عن فترة", callback_data="menu_report"),
        InlineKeyboardButton("6️⃣ حالة السوق (OpenAI)", callback_data="menu_market_status"),
    )
    return kb

# ----------------------- VERIFY KEYS -----------------------
async def verify_binance(api_key, secret_key):
    try:
        c = BinanceClient(api_key, secret_key)
        c.get_account()
        return True, "✅ Binance OK"
    except Exception as e:
        return False, f"❌ Binance: {e}"

async def verify_kucoin(api_key, secret_key, passphrase):
    try:
        t = KucoinTrade(api_key, secret_key, passphrase)
        acc = t.get_accounts()
        return (bool(acc), "✅ KuCoin OK" if acc else "❌ KuCoin: لا حسابات")
    except Exception as e:
        return False, f"❌ KuCoin: {e}"

async def verify_bybit(api_key, secret_key):
    try:
        from pybit.unified_trading import HTTP
        s = HTTP(api_key=api_key, api_secret=secret_key)
        r = s.get_wallet_balance(accountType="UNIFIED")
        ok = isinstance(r, dict) and r.get("retCode") == 0
        return (ok, "✅ Bybit OK" if ok else f"❌ Bybit: {r}")
    except ImportError:
        return False, "❌ Bybit: ثبّت pybit"
    except Exception as e:
        return False, f"❌ Bybit: {e}"

async def verify_okx(api_key, secret_key, passphrase):
    try:
        import okx.Account as Account
        accountAPI = Account.AccountAPI(api_key, secret_key, passphrase, use_server_time=False, flag="0")
        r = accountAPI.get_account_balance()
        ok = isinstance(r, dict) and str(r.get("code")) in ("0")
        return (ok, "✅ OKX OK" if ok else f"❌ OKX: {r}")
    except ImportError:
        return False, "❌ OKX: ثبّت okx"
    except Exception as e:
        return False, f"❌ OKX: {e}"

async def verify_kraken(api_key, secret_key):
    try:
        import krakenex
        k = krakenex.API(key=api_key, secret=secret_key)
        r = k.query_private('Balance')
        ok = isinstance(r, dict) and r.get("error") == []
        return (ok, "✅ Kraken OK" if ok else f"❌ Kraken: {r}")
    except ImportError:
        return False, "❌ Kraken: ثبّت krakenex"
    except Exception as e:
        return False, f"❌ Kraken: {e}"

# ----------------------- PRICE FEEDS (Public) -----------------------
def fetch_public_price(exchange: str) -> float:
    try:
        if exchange == "binance":
            r = requests.get("https://api.binance.com/api/v3/ticker/price", params={"symbol": "BTCUSDT"}, timeout=5)
            return float(r.json()["price"])
        if exchange == "kucoin":
            r = requests.get("https://api.kucoin.com/api/v1/market/orderbook/level1", params={"symbol": "BTC-USDT"}, timeout=5)
            return float(r.json()["data"]["price"])
        if exchange == "bybit":
            r = requests.get("https://api.bybit.com/v5/market/tickers", params={"category": "spot", "symbol": "BTCUSDT"}, timeout=5)
            return float(r.json()["result"]["list"][0]["lastPrice"])
        if exchange == "okx":
            r = requests.get("https://www.okx.com/api/v5/market/ticker", params={"instId": "BTC-USDT"}, timeout=5)
            return float(r.json()["data"][0]["last"])
        if exchange == "kraken":
            r = requests.get("https://api.kraken.com/0/public/Ticker", params={"pair": "XBTUSDT"}, timeout=5)
            data = r.json()["result"]
            k = list(data.keys())[0]
            return float(data[k]["c"][0])
        return None
    except Exception:
        return None

# ----------------------- EXECUTION ADAPTERS -----------------------
class ExecError(Exception):
    pass

class ExchangeExec:
    """Adapter لكل منصة: buy_market / sell_market لرمز BTC/USDT فقط."""
    def __init__(self, name: str, user: User):
        self.name = name
        self.user = user
        self.ok = True

        if name == "binance":
            if not (user.binance_api and user.binance_secret): self.ok = False
            else:
                self.client = BinanceClient(user.binance_api, user.binance_secret)

        elif name == "kucoin":
            if not (user.kucoin_api and user.kucoin_secret and user.kucoin_passphrase): self.ok = False
            else:
                self.market = KucoinMarket()
                self.trade = KucoinTrade(user.kucoin_api, user.kucoin_secret, user.kucoin_passphrase)

        elif name == "bybit":
            try:
                from pybit.unified_trading import HTTP
                if not (user.bybit_api and user.bybit_secret): self.ok = False
                else:
                    self.session = HTTP(api_key=user.bybit_api, api_secret=user.bybit_secret)
            except Exception:
                self.ok = False

        elif name == "okx":
            try:
                import okx.Trade as OKXTrade
                if not (user.okx_api and user.okx_secret and user.okx_passphrase): self.ok = False
                else:
                    self.okx_trade = OKXTrade.TradeAPI(user.okx_api, user.okx_secret, user.okx_passphrase, False, "0")
            except Exception:
                self.ok = False

        elif name == "kraken":
            try:
                import krakenex
                if not (user.kraken_api and user.kraken_secret): self.ok = False
                else:
                    self.kraken = krakenex.API(key=user.kraken_api, secret=user.kraken_secret)
            except Exception:
                self.ok = False

        else:
            self.ok = False

    def buy_market(self, qty_btc: float):
        if not self.ok:
            raise ExecError(f"{self.name} exec not ready")

        if self.name == "binance":
            return self.client.order_market_buy(symbol="BTCUSDT", quantity=round(qty_btc, 6))

        if self.name == "kucoin":
            # KuCoin spot size كعملة الأساس BTC
            return self.trade.create_market_order('BTC-USDT', 'buy', size=str(round(qty_btc, 6)))

        if self.name == "bybit":
            # Bybit spot size هي كمية BTC
            return self.session.place_order(category="spot", symbol="BTCUSDT", side="Buy", orderType="Market", qty=str(round(qty_btc, 6)))

        if self.name == "okx":
            # OKX mkt order: instId, side, ordType, sz (بحجم BTC)
            return self.okx_trade.place_order(instId="BTC-USDT", tdMode="cash", side="buy", ordType="market", sz=str(round(qty_btc, 6)))

        if self.name == "kraken":
            # Kraken pair XBTUSDT و volume بعدد XBT
            return self.kraken.query_private('AddOrder', data={"pair": "XBTUSDT", "type": "buy", "ordertype": "market", "volume": str(round(qty_btc, 6))})

        raise ExecError("Unsupported exchange")

    def sell_market(self, qty_btc: float):
        if not self.ok:
            raise ExecError(f"{self.name} exec not ready")

        if self.name == "binance":
            return self.client.order_market_sell(symbol="BTCUSDT", quantity=round(qty_btc, 6))

        if self.name == "kucoin":
            return self.trade.create_market_order('BTC-USDT', 'sell', size=str(round(qty_btc, 6)))

        if self.name == "bybit":
            return self.session.place_order(category="spot", symbol="BTCUSDT", side="Sell", orderType="Market", qty=str(round(qty_btc, 6)))

        if self.name == "okx":
            return self.okx_trade.place_order(instId="BTC-USDT", tdMode="cash", side="sell", ordType="market", sz=str(round(qty_btc, 6)))

        if self.name == "kraken":
            return self.kraken.query_private('AddOrder', data={"pair": "XBTUSDT", "type": "sell", "ordertype": "market", "volume": str(round(qty_btc, 6))})

        raise ExecError("Unsupported exchange")

# تقدير عمولات بسيطة/انزلاق: يمكن تعديلها لكل منصة
FEE_MAP = {
    "binance": 0.001,  # 0.1%
    "kucoin": 0.001,
    "bybit": 0.001,
    "okx": 0.001,
    "kraken": 0.0016,
}

def effective_spread(buy_ex:str, buy_price:float, sell_ex:str, sell_price:float):
    """صافي الفرق بعد خصم رسوم تقريبية على الجانبين."""
    buy_fee = FEE_MAP.get(buy_ex, 0.001)
    sell_fee = FEE_MAP.get(sell_ex, 0.001)
    # سعر شراء فعلي أعلى قليلًا، وسعر بيع فعلي أقل قليلًا
    eff_buy = buy_price * (1 + buy_fee)
    eff_sell = sell_price * (1 - sell_fee)
    return eff_sell - eff_buy

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
    await message.answer("أهلاً بك في بوت المراجحة 👋 اختر من القائمة:", reply_markup=main_menu_keyboard())

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
    platform = call.data.split("_")[1]  # binance/kucoin/bybit/okx/kraken/coinbase
    await state.update_data(selected_platform=platform)
    await call.answer()
    needs_passphrase = platform in ("kucoin", "okx", "coinbase")
    await call.message.edit_text(f"أرسل مفتاح API الخاص بمنصة {platform.capitalize()}:")
    await Form.waiting_api_key.set()
    await state.update_data(needs_passphrase=needs_passphrase)

@dp.message_handler(state=Form.waiting_api_key)
async def api_key_received(message: types.Message, state: FSMContext):
    api_key = message.text.strip()
    await state.update_data(api_key=api_key)
    data = await state.get_data()
    platform = data["selected_platform"]
    await message.answer(f"أرسل الـ Secret Key الخاص بـ {platform.capitalize()}:")
    await Form.waiting_secret_key.set()

@dp.message_handler(state=Form.waiting_secret_key)
async def secret_key_received(message: types.Message, state: FSMContext):
    secret_key = message.text.strip()
    await state.update_data(secret_key=secret_key)
    data = await state.get_data()
    if data.get("needs_passphrase", False):
        await message.answer(f"أرسل الـ Passphrase الخاص بـ {data['selected_platform'].capitalize()}:")
        await Form.waiting_passphrase.set()
    else:
        await handle_platform_save(message, state, passphrase=None)

@dp.message_handler(state=Form.waiting_passphrase)
async def passphrase_received(message: types.Message, state: FSMContext):
    passphrase = message.text.strip()
    await handle_platform_save(message, state, passphrase)

async def handle_platform_save(message: types.Message, state: FSMContext, passphrase: str = None):
    data = await state.get_data()
    platform = data["selected_platform"]
    api_key = data["api_key"]
    secret_key = data["secret_key"]

    # تحقق
    if platform == "binance":
        ok, msg = await verify_binance(api_key, secret_key)
    elif platform == "kucoin":
        ok, msg = await verify_kucoin(api_key, secret_key, passphrase or "")
    elif platform == "bybit":
        ok, msg = await verify_bybit(api_key, secret_key)
    elif platform == "okx":
        ok, msg = await verify_okx(api_key, secret_key, passphrase or "")
    elif platform == "kraken":
        ok, msg = await verify_kraken(api_key, secret_key)
    elif platform == "coinbase":
        ok, msg = False, "⚠️ Coinbase للعرض فقط حالياً."
    else:
        ok, msg = False, "منصة غير معروفة."

    if not ok:
        await message.answer(f"{msg}\n\n❌ فشل التحقق. تأكد من الصلاحيات (قراءة وتداول) ثم أعد المحاولة.")
        await state.finish()
        return

    # حفظ
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
    if platform == "binance":
        user.binance_api, user.binance_secret, user.binance_active = api_key, secret_key, True
    elif platform == "kucoin":
        user.kucoin_api, user.kucoin_secret, user.kucoin_passphrase, user.kucoin_active = api_key, secret_key, passphrase, True
    elif platform == "bybit":
        user.bybit_api, user.bybit_secret, user.bybit_active = api_key, secret_key, True
    elif platform == "okx":
        user.okx_api, user.okx_secret, user.okx_passphrase, user.okx_active = api_key, secret_key, passphrase, True
    elif platform == "kraken":
        user.kraken_api, user.kraken_secret, user.kraken_active = api_key, secret_key, True
    elif platform == "coinbase":
        user.coinbase_api, user.coinbase_secret, user.coinbase_passphrase, user.coinbase_active = api_key, secret_key, passphrase, True

    db.add(user)
    db.commit()
    db.close()

    await message.answer(f"{msg}\n\n✅ تم ربط {platform.capitalize()} بنجاح!")
    await state.finish()
    await message.answer("العودة للقائمة الرئيسية:", reply_markup=main_menu_keyboard())

# --------- مبلغ الاستثمار ---------
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

# --------- تقارير ---------
@dp.callback_query_handler(lambda c: c.data == "menu_report")
async def report_start_handler(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.edit_text("📅 أرسل تاريخ بداية الفترة (مثلاً: 2025-08-01):")
    await Form.waiting_report_start.set()

@dp.message_handler(state=Form.waiting_report_start)
async def report_start_date_received(message: types.Message, state: FSMContext):
    try:
        start_date = datetime.strptime(message.text.strip(), "%Y-%m-%d")
        await state.update_data(report_start=start_date)
        await message.answer("📅 أرسل تاريخ نهاية الفترة (مثلاً: 2025-08-10):")
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
        total_profit = 0.0
        for t in trades:
            report_text += f"{t.timestamp.date()} - {t.trade_type} - ربح: {t.profit:.4f} USDT\n"
            total_profit += t.profit
        report_text += f"\n💰 إجمالي الربح: {total_profit:.4f} USDT"
        await message.answer(report_text)
        await state.finish()
    except Exception:
        await message.answer("❌ تنسيق التاريخ غير صحيح. استخدم: YYYY-MM-DD")

# --------- حالة السوق (OpenAI) ---------
async def get_market_analysis():
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful crypto market analyst."},
                {"role": "user", "content": (
                    "اعطني ملخص تحليل سوق العملات الرقمية الحالي، مع أسعار BTC و ETH،"
                    " وتوقعات بناء على مؤشرات تقنية مثل RSI و MACD. اذكر التحذيرات إن وجدت."
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

# --------- START/STOP ---------
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
        await call.answer("❌ لم تحدد مبلغ الاستثمار. اضبط المبلغ أولًا.")
        db.close()
        return

    user.investment_status = "started"
    db.add(user)
    db.commit()
    db.close()
    await call.answer()
    await call.message.edit_text("🚀 تم بدء الاستثمار والمراجحة التلقائية. يمكنك إيقافه من القائمة.")
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

# --------- ARBITRAGE LOOP ---------
EXECUTABLE_EXCHANGES = ["binance", "kucoin", "bybit", "okx", "kraken"]

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
            # منصات مفعلة
            actives = []
            if user.binance_active: actives.append("binance")
            if user.kucoin_active: actives.append("kucoin")
            if user.bybit_active: actives.append("bybit")
            if user.okx_active: actives.append("okx")
            if user.kraken_active: actives.append("kraken")
            if len(actives) < 2:
                await bot.send_message(user.telegram_id, "❌ يجب أن تبقى منصتان على الأقل مفعّلتين.")
                user.investment_status = "stopped"
                db.add(user); db.commit()
                db.close()
                return

            # أسعار عامة
            prices = {ex: fetch_public_price(ex) for ex in actives}
            prices = {ex: p for ex, p in prices.items() if p}
            if len(prices) < 2:
                await bot.send_message(user.telegram_id, "لا توجد أسعار كافية حالياً.")
                await asyncio.sleep(60)
                continue

            # اختر أفضل فرصة: أقل سعر شراء وأعلى سعر بيع
            buy_on = min(prices, key=prices.get)
            sell_on = max(prices, key=prices.get)
            buy_price = prices[buy_on]
            sell_price = prices[sell_on]

            # صافي الفرق بعد تقدير الرسوم
            net_spread = effective_spread(buy_on, buy_price, sell_on, sell_price)

            # حد أدنى للجدوى (بعد الرسوم) – يمكنك تغييره
            min_usdt_edge = 15.0

            min_price = min(buy_price, sell_price)
            qty_btc = user.investment_amount / min_price if min_price else 0.0

            if net_spread > 0 and (net_spread * qty_btc) >= min_usdt_edge and qty_btc > 0:
                # لازم المنصتين قابلتين للتنفيذ
                if buy_on in EXECUTABLE_EXCHANGES and sell_on in EXECUTABLE_EXCHANGES:
                    buy_exec = ExchangeExec(buy_on, user)
                    sell_exec = ExchangeExec(sell_on, user)

                    if not (buy_exec.ok and sell_exec.ok):
                        await bot.send_message(user.telegram_id, f"⚠️ فرصة متاحة لكن التنفيذ غير جاهز ({buy_on}->{sell_on}).")
                    else:
                        # تنفيذ متتابع بسيط (يفضل لاحقاً استخدام hedge/atomic أو تمويل على نفس المنصة)
                        buy_exec.buy_market(qty_btc)
                        sell_exec.sell_market(qty_btc)

                        profit = net_spread * qty_btc
                        trade_type = f"Arb Buy {buy_on.upper()} / Sell {sell_on.upper()}"
                        log = TradeLog(user_id=user.id, trade_type=trade_type, amount=qty_btc, price=min_price, profit=profit)
                        db.add(log); db.commit()
                        await bot.send_message(user.telegram_id, f"✅ {trade_type} | qty={qty_btc:.6f} | صافي ربح تقديري: {profit:.4f} USDT")
                else:
                    await bot.send_message(user.telegram_id, f"💡 فرصة مراجحة بين {buy_on.upper()} و {sell_on.upper()} (التنفيذ غير مفعل لهما).")
            else:
                await bot.send_message(user.telegram_id, "لا توجد فرصة مراجحة مناسبة حالياً.")

        except Exception as e:
            await bot.send_message(user.telegram_id, f"❌ خطأ في المراجحة: {str(e)}")

        # تكرار كل 60 ثانية
        await asyncio.sleep(60)

# ----------------------- RUN -----------------------
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
