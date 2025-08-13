import os
import asyncio
import logging
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from sqlalchemy import create_engine, Column, BigInteger, Integer, String, Float, DateTime, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker

import ccxt
import openai

logging.basicConfig(level=logging.INFO)

# ----------------------- ENV -----------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Webhook إعدادات
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # مثال: https://your-railway-domain.up.railway.app/webhook/<bot-token>
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", "8080"))

# إعدادات المراجحة
ARBITRAGE_SYMBOL = os.getenv("ARBITRAGE_SYMBOL", "BTC/USDT")
ARBITRAGE_THRESHOLD_USD = float(os.getenv("ARBITRAGE_THRESHOLD_USD", "20"))  # أدنى فرق سعر بالدولار لتنفيذ المراجحة
DEFAULT_TAKER_FEE = float(os.getenv("DEFAULT_TAKER_FEE", "0.001"))  # 0.1% افتراضي
BOT_FEE_PCT = float(os.getenv("BOT_FEE_PCT", "0.002"))  # 0.2% افتراضي
LOOP_SLEEP_SECONDS = int(os.getenv("LOOP_SLEEP_SECONDS", "30"))

if not BOT_TOKEN or not DATABASE_URL or not OPENAI_API_KEY or not WEBHOOK_URL:
    raise Exception("❌ Missing required env: BOT_TOKEN, DATABASE_URL, OPENAI_API_KEY, WEBHOOK_URL")

openai.api_key = OPENAI_API_KEY

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# ----------------------- DB -----------------------
Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, index=True)

    # Binance
    binance_api = Column(String(512), nullable=True)
    binance_secret = Column(String(512), nullable=True)
    binance_active = Column(Boolean, default=False)

    # KuCoin
    kucoin_api = Column(String(512), nullable=True)
    kucoin_secret = Column(String(512), nullable=True)
    kucoin_passphrase = Column(String(512), nullable=True)
    kucoin_active = Column(Boolean, default=False)

    # Bybit
    bybit_api = Column(String(512), nullable=True)
    bybit_secret = Column(String(512), nullable=True)
    bybit_active = Column(Boolean, default=False)

    # OKX
    okx_api = Column(String(512), nullable=True)
    okx_secret = Column(String(512), nullable=True)
    okx_passphrase = Column(String(512), nullable=True)
    okx_active = Column(Boolean, default=False)

    # Kraken
    kraken_api = Column(String(512), nullable=True)
    kraken_secret = Column(String(512), nullable=True)
    kraken_active = Column(Boolean, default=False)

    # Coinbase (Advanced)
    coinbase_api = Column(String(512), nullable=True)
    coinbase_secret = Column(String(512), nullable=True)
    coinbase_passphrase = Column(String(512), nullable=True)
    coinbase_active = Column(Boolean, default=False)

    investment_amount = Column(Float, default=0.0)  # مبلغ الاستثمار بالـ USDT
    investment_status = Column(String(20), default="stopped")

class TradeLog(Base):
    __tablename__ = "trade_logs"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    trade_type = Column(String(80))          # "Buy X / Sell Y"
    platform_buy = Column(String(32))
    platform_sell = Column(String(32))
    symbol = Column(String(32))
    amount = Column(Float)                   # كمية BTC مثلاً
    price_buy = Column(Float)
    price_sell = Column(Float)
    taker_fee_buy = Column(Float)
    taker_fee_sell = Column(Float)
    bot_fee = Column(Float)
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

# ----------------------- Helpers: CCXT -----------------------
def make_exchange(id_: str, api=None, secret=None, password=None):
    """ينشئ عميل CCXT مضبوط بالمفاتيح إن وُجدت (للاستخدام في التداول)،
       أو عميل عام بدون مفاتيح (للأسعار فقط)."""
    params = {"enableRateLimit": True}
    if api and secret:
        params.update({"apiKey": api, "secret": secret})
    if password:
        params.update({"password": password})

    # خرائط IDs متوافقة مع CCXT
    mapping = {
        "binance": "binance",
        "kucoin": "kucoin",
        "bybit": "bybit",
        "okx": "okx",
        "kraken": "kraken",
        "coinbase": "coinbase",  # CCXT الحديثة تدعم Coinbase Advanced باسم 'coinbase'
    }
    ex_id = mapping[id_.lower()]
    ex_class = getattr(ccxt, ex_id)
    ex = ex_class(params)
    return ex

def get_user_active_exchanges(user: User):
    """يرجع قائمة (اسم المنصة، كائن ccxt، has_keys) للمنصات المفعلة عند المستخدم"""
    exs = []
    # Binance
    if user.binance_active:
        exs.append(("Binance", make_exchange("binance", user.binance_api, user.binance_secret, None), bool(user.binance_api and user.binance_secret)))
    # KuCoin
    if user.kucoin_active:
        exs.append(("KuCoin", make_exchange("kucoin", user.kucoin_api, user.kucoin_secret, user.kucoin_passphrase), bool(user.kucoin_api and user.kucoin_secret and user.kucoin_passphrase)))
    # Bybit
    if user.bybit_active:
        exs.append(("Bybit", make_exchange("bybit", user.bybit_api, user.bybit_secret, None), bool(user.bybit_api and user.bybit_secret)))
    # OKX
    if user.okx_active:
        exs.append(("OKX", make_exchange("okx", user.okx_api, user.okx_secret, user.okx_passphrase), bool(user.okx_api and user.okx_secret and user.okx_passphrase)))
    # Kraken
    if user.kraken_active:
        exs.append(("Kraken", make_exchange("kraken", user.kraken_api, user.kraken_secret, None), bool(user.kraken_api and user.kraken_secret)))
    # Coinbase
    if user.coinbase_active:
        exs.append(("Coinbase", make_exchange("coinbase", user.coinbase_api, user.coinbase_secret, user.coinbase_passphrase), bool(user.coinbase_api and user.coinbase_secret and user.coinbase_passphrase)))
    return exs

async def verify_keys_ccxt(exchange: ccxt.Exchange) -> bool:
    try:
        # بعض المنصات تحتاج load_markets قبل balance
        await asyncio.to_thread(exchange.load_markets)
        bal = await asyncio.to_thread(exchange.fetch_balance)
        return bool(bal)
    except Exception:
        return False

def taker_fee_of(exchange: ccxt.Exchange, symbol: str) -> float:
    try:
        markets = exchange.markets or exchange.load_markets()
        m = markets.get(symbol)
        if m and "taker" in m and m["taker"]:
            return float(m["taker"])
    except Exception:
        pass
    return DEFAULT_TAKER_FEE

def normalize_symbol(exchange: ccxt.Exchange, symbol: str) -> str:
    """يحاول استخدام الرمز الموحد، ولو مش متاح يحاول بدائل شائعة (مثلاً Kraken)"""
    # محاولات شائعة للـ BTC/USDT
    candidates = [symbol, "XBT/USDT", "BTC/USDT:USDT"]  # بعض المنصات تذيّل العقد
    try:
        markets = exchange.markets or exchange.load_markets()
        for s in candidates:
            if s in markets:
                return s
    except Exception:
        pass
    return symbol  # بنرجّع الأصلي ونترك الفشل يعالج لاحقاً

# ----------------------- Keyboards -----------------------
def main_menu_keyboard():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("1️⃣ تسجيل/تعديل بيانات التداول", callback_data="menu_edit_trading_data"),
        InlineKeyboardButton("2️⃣ ابدأ استثمار", callback_data="menu_start_invest"),
        InlineKeyboardButton("3️⃣ استثمار وهمي", callback_data="menu_fake_invest"),
        InlineKeyboardButton("4️⃣ كشف حساب عن فترة", callback_data="menu_report"),
        InlineKeyboardButton("5️⃣ حالة السوق", callback_data="menu_market_status"),
        InlineKeyboardButton("6️⃣ إيقاف الاستثمار", callback_data="menu_stop_invest"),
        InlineKeyboardButton("⚙️ اختبار مفاتيح منصة", callback_data="test_platform_prompt"),
    )
    return kb

def user_platforms_keyboard(user: User):
    kb = InlineKeyboardMarkup(row_width=2)
    platforms = [
        ("Binance", user.binance_active, user.binance_api),
        ("KuCoin", user.kucoin_active, user.kucoin_api),
        ("Bybit", user.bybit_active, user.bybit_api),
        ("OKX", user.okx_active, user.okx_api),
        ("Kraken", user.kraken_active, user.kraken_api),
        ("Coinbase", user.coinbase_active, user.coinbase_api),
    ]
    for name, active, api in platforms:
        text = ("✅ " if active else "❌ ") + name + (" (مربوط)" if api else " (غير مربوط)")
        kb.insert(InlineKeyboardButton(text, callback_data=f"platform_{name.lower()}"))
    kb.add(InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu"))
    return kb

# ----------------------- Handlers: Start / Menu -----------------------
@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
    if not user:
        user = User(telegram_id=message.from_user.id)
        db.add(user)
        db.commit()
    db.close()
    await message.answer("أهلاً بك في بوت المراجحة 👋\nاختر من القائمة:", reply_markup=main_menu_keyboard())

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
    await call.message.edit_text("اختر المنصة لإضافة/تعديل مفاتيح API أو تفعيل/إيقاف:", reply_markup=user_platforms_keyboard(user))

# ----------------------- Handlers: Platform selection & API entry -----------------------
class PlatformNames:
    NEED_PASSPHRASE = {"kucoin", "okx", "coinbase"}

@dp.callback_query_handler(lambda c: c.data.startswith("platform_"))
async def platform_selected(call: types.CallbackQuery, state: FSMContext):
    platform = call.data.split("_", 1)[1]  # binance/kucoin/bybit/okx/kraken/coinbase
    await state.update_data(selected_platform=platform)
    await call.answer()
    await call.message.edit_text(f"أرسل مفتاح API الخاص بمنصة {platform.capitalize()}:")
    await Form.waiting_api_key.set()

@dp.message_handler(state=Form.waiting_api_key)
async def api_key_received(message: types.Message, state: FSMContext):
    data = await state.get_data()
    platform = data["selected_platform"]
    api_key = message.text.strip()
    await state.update_data(api_key=api_key)
    await message.answer(f"أرسل Secret Key الخاص بـ {platform.capitalize()}:")
    await Form.waiting_secret_key.set()

@dp.message_handler(state=Form.waiting_secret_key)
async def secret_key_received(message: types.Message, state: FSMContext):
    data = await state.get_data()
    platform = data["selected_platform"]
    secret_key = message.text.strip()
    await state.update_data(secret_key=secret_key)

    if platform in PlatformNames.NEED_PASSPHRASE:
        await message.answer(f"أرسل Passphrase الخاص بـ {platform.capitalize()}:")
        await Form.waiting_passphrase.set()
    else:
        # تحقق وحفظ
        await save_platform_keys(message, state, platform, passphrase=None)

@dp.message_handler(state=Form.waiting_passphrase)
async def passphrase_received(message: types.Message, state: FSMContext):
    data = await state.get_data()
    platform = data["selected_platform"]
    passphrase = message.text.strip()
    await save_platform_keys(message, state, platform, passphrase=passphrase)

async def save_platform_keys(message: types.Message, state: FSMContext, platform: str, passphrase: str = None):
    data = await state.get_data()
    api_key = data["api_key"]
    secret_key = data["secret_key"]

    # تحقّق سريع بالمفاتيح عن طريق CCXT
    try:
        ex = make_exchange(platform, api_key, secret_key, passphrase)
        ok = await verify_keys_ccxt(ex)
    except Exception:
        ok = False

    if not ok:
        await message.answer("❌ المفاتيح غير صحيحة أو غير مفعلة للتداول/القراءة. تأكد من الصلاحيات وأعد المحاولة.")
        await state.finish()
        return

    # حفظ في DB
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=message.from_user.id).first()

    platform = platform.lower()
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

    await message.answer(f"✅ تم ربط {platform.capitalize()} بنجاح!", reply_markup=main_menu_keyboard())
    await state.finish()

# ----------------------- Handlers: Start/Stop invest -----------------------
@dp.callback_query_handler(lambda c: c.data == "menu_start_invest")
async def start_invest_handler(call: types.CallbackQuery):
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=call.from_user.id).first()

    # لازم على الأقل منصة واحدة مفعّلة ومفاتيح صالحة
    active_exs = [n for n, ex, has in get_user_active_exchanges(user) if has]
    if not active_exs:
        await call.answer("❌ لم تقم بربط أي منصة تداول بمفاتيح صالحة.")
        db.close()
        return

    # لو مفيش مبلغ استثمار، هنطلبه
    if user.investment_amount <= 0:
        await call.answer()
        await call.message.edit_text("💵 أرسل مبلغ الاستثمار بالـ USDT (مثال: 100):")
        await Form.waiting_investment_amount.set()
        db.close()
        return

    user.investment_status = "started"
    db.add(user)
    db.commit()
    db.close()

    await call.answer()
    await call.message.edit_text("🚀 تم بدء الاستثمار والمراجحة تلقائيًا. استخدم 'إيقاف الاستثمار' لإيقافه.", reply_markup=main_menu_keyboard())
    asyncio.create_task(run_arbitrage_loop(call.from_user.id))

@dp.message_handler(state=Form.waiting_investment_amount)
async def investment_amount_received(message: types.Message, state: FSMContext):
    try:
        amt = float(message.text.strip())
        if amt <= 0:
            raise ValueError
        db = SessionLocal()
        user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
        user.investment_amount = amt
        db.add(user)
        db.commit()
        db.close()
        await state.finish()
        await message.answer(f"✅ تم حفظ مبلغ الاستثمار: {amt:.2f} USDT.\nاضغط 'ابدأ استثمار' للانطلاق.", reply_markup=main_menu_keyboard())
    except Exception:
        await message.answer("❌ رجاءً أرسل رقمًا صحيحًا أكبر من 0.")

@dp.callback_query_handler(lambda c: c.data == "menu_stop_invest")
async def stop_invest_handler(call: types.CallbackQuery):
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=call.from_user.id).first()
    user.investment_status = "stopped"
    db.add(user)
    db.commit()
    db.close()
    await call.answer()
    await call.message.edit_text("⏸️ تم إيقاف الاستثمار.", reply_markup=main_menu_keyboard())

# ----------------------- تقرير فترة -----------------------
@dp.callback_query_handler(lambda c: c.data == "menu_report")
async def report_start_handler(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.edit_text("📅 أرسل تاريخ البداية (YYYY-MM-DD):")
    await Form.waiting_report_start.set()

@dp.message_handler(state=Form.waiting_report_start)
async def report_start_date_received(message: types.Message, state: FSMContext):
    try:
        start_date = datetime.strptime(message.text.strip(), "%Y-%m-%d")
        await state.update_data(report_start=start_date)
        await message.answer("📅 أرسل تاريخ النهاية (YYYY-MM-DD):")
        await Form.waiting_report_end.set()
    except Exception:
        await message.answer("❌ صيغة التاريخ غير صحيحة. استخدم: YYYY-MM-DD")

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
            await message.answer("لا توجد صفقات في هذه الفترة.")
            await state.finish()
            return

        total_profit = sum(t.profit for t in trades)
        lines = [f"📊 كشف حساب {start_date.date()} → {end_date.date()}:"]
        for t in trades:
            lines.append(
                f"{t.timestamp.date()} • {t.trade_type} • {t.symbol} • كمية: {t.amount:.6f} • ربح: {t.profit:.4f} USDT"
            )
        lines.append(f"\n💰 إجمالي الربح: {total_profit:.4f} USDT")
        await message.answer("\n".join(lines))
        await state.finish()
    except Exception:
        await message.answer("❌ صيغة التاريخ غير صحيحة. استخدم: YYYY-MM-DD")

# ----------------------- حالة السوق (OpenAI) -----------------------
async def get_market_analysis():
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful crypto market analyst."},
                {"role": "user", "content":
                 "اعطني ملخص تحليل سوق العملات الرقمية الحالي، مع أسعار لبعض الأزواج الرئيسية مثل BTC/USDT و ETH/USDT،"
                 " ونبذة عن التوقعات بناءً على مؤشرات RSI و MACD، واذكر التحذيرات إن وجدت."
                 }
            ],
            max_tokens=350,
            temperature=0.7
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"❌ تعذّر جلب تحليل السوق: {e}"

@dp.callback_query_handler(lambda c: c.data == "menu_market_status")
async def market_status_handler(call: types.CallbackQuery):
    await call.answer()
    analysis_text = await get_market_analysis()
    await call.message.edit_text(analysis_text, reply_markup=main_menu_keyboard())

# ----------------------- اختبار مفاتيح منصة عامة -----------------------
@dp.callback_query_handler(lambda c: c.data == "test_platform_prompt")
async def test_platform_prompt_handler(call: types.CallbackQuery):
    await call.answer()
    await call.message.edit_text(
        "أرسل لاختبار مفاتيحك بهذه الصيغة:\n\n"
        "/test_keys <platform> <API_KEY> <SECRET> [PASSPHRASE]\n\n"
        "مثال:\n/test_keys kucoin abc def ghi\n/test_keys binance abc def"
    )

@dp.message_handler(commands=["test_keys"])
async def test_keys_handler(message: types.Message):
    parts = message.text.split()
    if len(parts) < 4:
        await message.answer("❌ الصيغة: /test_keys <platform> <API_KEY> <SECRET> [PASSPHRASE]")
        return
    platform = parts[1].lower()
    api_key, secret = parts[2], parts[3]
    passphrase = parts[4] if len(parts) > 4 else None
    try:
        ex = make_exchange(platform, api_key, secret, passphrase)
        ok = await verify_keys_ccxt(ex)
        await message.answer("✅ المفاتيح صالحة." if ok else "❌ المفاتيح غير صالحة.")
    except Exception as e:
        await message.answer(f"❌ خطأ: {e}")

# ----------------------- المراجحة التلقائية -----------------------
async def run_arbitrage_loop(user_telegram_id: int):
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=user_telegram_id).first()
    if not user:
        db.close()
        return

    while True:
        db.refresh(user)
        if user.investment_status != "started":
            db.close()
            return

        try:
            active = get_user_active_exchanges(user)
            tradables = [(name, ex) for name, ex, has in active if has]
            if len(tradables) < 1:
                await bot.send_message(user.telegram_id, "❌ لا توجد منصات مفعّلة بمفاتيح صالحة.")
                user.investment_status = "stopped"
                db.add(user)
                db.commit()
                db.close()
                return

            # حمّل الأسواق مرة واحدة لكل منصة + استرجع سعر السحب/العرض
            prices = {}
            for name, ex in tradables:
                try:
                    await asyncio.to_thread(ex.load_markets)
                    sym = normalize_symbol(ex, ARBITRAGE_SYMBOL)
                    ticker = await asyncio.to_thread(ex.fetch_ticker, sym)
                    ask = float(ticker.get("ask") or ticker.get("last") or 0)
                    bid = float(ticker.get("bid") or ticker.get("last") or 0)
                    if ask > 0 and bid > 0:
                        prices[name] = {"symbol": sym, "ask": ask, "bid": bid, "ex": ex}
                except Exception:
                    continue

            if len(prices) < 2:
                await asyncio.sleep(LOOP_SLEEP_SECONDS)
                continue

            # ابحث عن أفضل فرصة: شراء الأرخص (ask) وبيع الأغلى (bid)
            best_buy_name, best_sell_name = None, None
            best_buy_ask, best_sell_bid = 10**12, 0.0
            sym_use = ARBITRAGE_SYMBOL

            for name, info in prices.items():
                if info["ask"] < best_buy_ask:
                    best_buy_ask = info["ask"]
                    best_buy_name = name
                    sym_use = info["symbol"]
                if info["bid"] > best_sell_bid:
                    best_sell_bid = info["bid"]
                    best_sell_name = name

            # لازم تكون منصتين مختلفتين
            if not best_buy_name or not best_sell_name or best_buy_name == best_sell_name:
                await asyncio.sleep(LOOP_SLEEP_SECONDS)
                continue

            spread_usd = best_sell_bid - best_buy_ask
            if spread_usd < ARBITRAGE_THRESHOLD_USD:
                await asyncio.sleep(LOOP_SLEEP_SECONDS)
                continue

            ex_buy = prices[best_buy_name]["ex"]
            ex_sell = prices[best_sell_name]["ex"]

            # الرسوم (taker) لكل منصة
            fee_buy = taker_fee_of(ex_buy, sym_use)
            fee_sell = taker_fee_of(ex_sell, sym_use)

            # رصيد المستخدم
            # شراء يحتاج USDT في منصة الشراء، بيع يحتاج BTC في منصة البيع
            bal_buy = await asyncio.to_thread(ex_buy.fetch_balance)
            bal_sell = await asyncio.to_thread(ex_sell.fetch_balance)

            usdt_avail = float(bal_buy.get("free", {}).get("USDT", 0.0) or bal_buy.get("USDT", {}).get("free", 0.0) or 0.0)
            btc_avail = float(bal_sell.get("free", {}).get("BTC", 0.0) or bal_sell.get("BTC", {}).get("free", 0.0) or 0.0)

            invest_usdt = float(user.investment_amount or 0)
            if invest_usdt <= 0:
                invest_usdt = usdt_avail  # لو المستخدم ماحطش مبلغ، هنستعمل كل المتاح

            # كمية الشراء (BTC) بناءً على المتاح
            qty_by_invest = invest_usdt / best_buy_ask
            qty_cap_by_balance = usdt_avail / best_buy_ask
            # لازم يكون عندنا كمية للبيع كافية في المنصة الأخرى (لو هنبيع فورًا)
            qty_cap_sell_balance = btc_avail

            amount_to_trade = max(0.0, min(qty_by_invest, qty_cap_by_balance, qty_cap_sell_balance))

            if amount_to_trade <= 0:
                # مفيش رصيد كافي: هنبلّغ المستخدم ونكمل
                await bot.send_message(
                    user.telegram_id,
                    "ℹ️ فرصة مراجحة متاحة لكن الرصيد غير كافٍ (USDT في منصة الشراء أو BTC في منصة البيع)."
                )
                await asyncio.sleep(LOOP_SLEEP_SECONDS)
                continue

            # تقدير صافي الربح قبل التنفيذ
            gross_profit_usd = spread_usd * amount_to_trade
            fees_buy_usd = amount_to_trade * best_buy_ask * fee_buy
            fees_sell_usd = amount_to_trade * best_sell_bid * fee_sell
            bot_fee_usd = amount_to_trade * best_sell_bid * BOT_FEE_PCT
            net_profit = gross_profit_usd - fees_buy_usd - fees_sell_usd - bot_fee_usd

            if net_profit <= 0:
                await asyncio.sleep(LOOP_SLEEP_SECONDS)
                continue

            # تنفيذ السوق (Market) — شراء ثم بيع
            # ملاحظة: لو المنصة لا تدعم market أو الرمز مختلف، قد يرمي استثناء
            # شراء
            create_buy = await asyncio.to_thread(
                ex_buy.create_market_buy_order, sym_use, amount_to_trade
            )
            # بيع
            create_sell = await asyncio.to_thread(
                ex_sell.create_market_sell_order, sym_use, amount_to_trade
            )

            # حفظ السجل
            trade_log = TradeLog(
                user_id=user.id,
                trade_type=f"Buy {best_buy_name} / Sell {best_sell_name}",
                platform_buy=best_buy_name,
                platform_sell=best_sell_name,
                symbol=sym_use,
                amount=amount_to_trade,
                price_buy=best_buy_ask,
                price_sell=best_sell_bid,
                taker_fee_buy=fee_buy,
                taker_fee_sell=fee_sell,
                bot_fee=bot_fee_usd,
                profit=net_profit
            )
            db.add(trade_log)
            db.commit()

            # إشعار المستخدم
            msg = (
                f"✅ تمت صفقة مراجحة!\n"
                f"• شراء: {best_buy_name} @ {best_buy_ask:.2f}\n"
                f"• بيع: {best_sell_name} @ {best_sell_bid:.2f}\n"
                f"• الرمز: {sym_use}\n"
                f"• الكمية: {amount_to_trade:.6f}\n"
                f"• الرسوم (شراء): {fees_buy_usd:.4f} USDT\n"
                f"• الرسوم (بيع): {fees_sell_usd:.4f} USDT\n"
                f"• عمولة البوت: {bot_fee_usd:.4f} USDT\n"
                f"• الربح الصافي: {net_profit:.4f} USDT"
            )
            await bot.send_message(user.telegram_id, msg)

        except Exception as e:
            try:
                await bot.send_message(user.telegram_id, f"❌ خطأ في المراجحة: {e}")
            except Exception:
                pass

        await asyncio.sleep(LOOP_SLEEP_SECONDS)

# ----------------------- Webhook Startup/Shutdown -----------------------
async def on_startup(dp):
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(WEBHOOK_URL)
    logging.info(f"Webhook set to: {WEBHOOK_URL}")

async def on_shutdown(dp):
    await bot.delete_webhook()
    logging.info("Webhook deleted")

# ----------------------- RUN (Webhook) -----------------------
if __name__ == "__main__":
    executor.start_webhook(
        dispatcher=dp,
        webhook_path="/" + WEBHOOK_URL.split("/", 3)[-1],  # يسمح بتمرير كامل المسار من env
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
    )
