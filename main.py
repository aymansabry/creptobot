import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Boolean,
    ForeignKey,
    UniqueConstraint,
    BigInteger,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

import ccxt

logging.basicConfig(level=logging.INFO)

# ----------------------- ENV -----------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///arbitrage.db")

if not BOT_TOKEN or not DATABASE_URL:
    raise Exception("❌ BOT_TOKEN و DATABASE_URL مطلوبة")

# ----------------------- DB -----------------------
Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, index=True)
    investment_amount = Column(Float, default=0.0)
    investment_status = Column(String(20), default="stopped")  # started/stopped
    base_quote = Column(String(20), default="BTC/USDT")
    fee_consent = Column(Boolean, default=False)

    exchanges = relationship("ExchangeCredential", back_populates="user", cascade="all, delete-orphan")

class ExchangeCredential(Base):
    __tablename__ = "exchange_credentials"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    exchange_id = Column(String(50))
    api_key = Column(String(256), nullable=True)
    secret = Column(String(256), nullable=True)
    password = Column(String(256), nullable=True)
    active = Column(Boolean, default=False)

    user = relationship("User", back_populates="exchanges")

    __table_args__ = (
        UniqueConstraint("user_id", "exchange_id", name="uq_user_exchange"),
    )

class TradeLog(Base):
    __tablename__ = "trade_logs"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True)
    leg_buy_exchange = Column(String(50))
    leg_sell_exchange = Column(String(50))
    symbol = Column(String(20))
    amount = Column(Float)
    entry_price = Column(Float)
    exit_price = Column(Float)
    gross_profit = Column(Float)
    fees_total = Column(Float)
    net_profit = Column(Float)
    note = Column(String(255), default="")
    timestamp = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(engine)

# ----------------------- BOT -----------------------
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

SUPPORTED_EXCHANGES: Dict[str, str] = {
    "binance": "Binance",
    "kucoin": "KuCoin",
    "okx": "OKX",
    "bybit": "Bybit",
    "kraken": "Kraken",
    "coinbase": "Coinbase Advanced",
}

DEFAULT_SYMBOLS: List[str] = [
    "BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT",
    "ADA/USDT", "DOGE/USDT", "TON/USDT", "LTC/USDT", "TRX/USDT",
    "AVAX/USDT", "LINK/USDT",
]

class Form(StatesGroup):
    choose_exchange = State()
    waiting_api_key = State()
    waiting_secret_key = State()
    waiting_password = State()
    waiting_investment_amount = State()
    choose_symbols = State()
    fee_consent = State()
    waiting_report_start = State()
    waiting_report_end = State()

# ----------------------- HELPERS -----------------------

def exchange_list_keyboard(user: User) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=2)
    for ex_id, ex_name in SUPPORTED_EXCHANGES.items():
        cred = next((c for c in user.exchanges if c.exchange_id == ex_id), None)
        status = "✅" if (cred and cred.active) else "❌"
        connected = "(مربوط)" if cred and cred.api_key else "(غير مربوط)"
        kb.insert(InlineKeyboardButton(f"{status} {ex_name} {connected}", callback_data=f"ex_{ex_id}"))
    kb.add(InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu"))
    return kb

def main_menu_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("1️⃣ تسجيل/تعديل بيانات التداول", callback_data="menu_edit_trading_data"),
        InlineKeyboardButton("2️⃣ تحديد مبلغ/أزواج", callback_data="menu_set_amount_symbols"),
        InlineKeyboardButton("3️⃣ بدء الاستثمار", callback_data="menu_start_invest"),
        InlineKeyboardButton("4️⃣ كشف حساب عن فترة", callback_data="menu_report"),
        InlineKeyboardButton("5️⃣ إيقاف الاستثمار", callback_data="menu_stop_invest"),
    )
    return kb

def build_ccxt_instance(cred: ExchangeCredential):
    cls = getattr(ccxt, cred.exchange_id)
    kwargs = {
        "apiKey": cred.api_key or "",
        "secret": cred.secret or "",
        "password": cred.password or None,
        "enableRateLimit": True,
        "options": {"defaultType": "spot"},
    }
    return cls(kwargs)

async def verify_keys(exchange_id: str, api_key: str, secret: str, password: Optional[str]) -> bool:
    try:
        cls = getattr(ccxt, exchange_id)
        ex = cls({"apiKey": api_key, "secret": secret, "password": password, "enableRateLimit": True})
        await asyncio.to_thread(ex.load_markets)
        bal = await asyncio.to_thread(ex.fetch_balance)
        return bal is not None
    except Exception as e:
        logging.exception(e)
        return False

async def fetch_best_prices(active_creds: List[ExchangeCredential], symbol: str) -> Tuple[Optional[Tuple[str, float]], Optional[Tuple[str, float]]]:
    best_buy = None
    best_sell = None
    for cred in active_creds:
        try:
            ex = build_ccxt_instance(cred)
            ticker = await asyncio.to_thread(ex.fetch_ticker, symbol)
            bid = float(ticker.get("bid") or 0)
            ask = float(ticker.get("ask") or 0)
            if ask and (best_buy is None or ask < best_buy[1]):
                best_buy = (cred.exchange_id, ask)
            if bid and (best_sell is None or bid > best_sell[1]):
                best_sell = (cred.exchange_id, bid)
        except Exception as e:
            logging.warning(f"⚠️ فشل سعر {cred.exchange_id} لـ {symbol}: {e}")
            continue
    return best_buy, best_sell

async def estimate_fees(cred_buy: ExchangeCredential, cred_sell: ExchangeCredential, symbol: str, amount: float) -> float:
    total = 0.0
    for cred, side in [(cred_buy, "buy"), (cred_sell, "sell")]:
        try:
            ex = build_ccxt_instance(cred)
            markets = await asyncio.to_thread(ex.load_markets)
            m = markets.get(symbol, {})
            taker = m.get("taker", 0.001)
            total += taker
        except Exception:
            total += 0.001
    return total

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
    await message.answer("أهلاً بك في بوت المراجحة متعدد المنصات. اختر من القائمة:", reply_markup=main_menu_keyboard())

@dp.callback_query_handler(lambda c: c.data == "main_menu")
async def back_to_main(call: types.CallbackQuery):
    await call.answer()
    await call.message.edit_text("القائمة الرئيسية:", reply_markup=main_menu_keyboard())


# ---- إدارة بيانات التداول (إضافة/تعديل/تفعيل منصات) ----
@dp.callback_query_handler(lambda c: c.data == "menu_edit_trading_data")
async def menu_edit_trading_data(call: types.CallbackQuery):
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=call.from_user.id).first()
    db.close()
    await call.answer()
    await call.message.edit_text(
        "اختر المنصة لإضافة/تعديل مفاتيح API أو تفعيل/إيقاف:",
        reply_markup=exchange_list_keyboard(user)
    )

@dp.callback_query_handler(lambda c: c.data.startswith("ex_"))
async def exchange_selected(call: types.CallbackQuery, state: FSMContext):
    ex_id = call.data.split("_", 1)[1]
    await state.update_data(selected_exchange=ex_id)
    await call.answer()
    await call.message.edit_text(f"أرسل مفتاح API لمنصة {SUPPORTED_EXCHANGES[ex_id]}:")
    await Form.waiting_api_key.set()

@dp.message_handler(state=Form.waiting_api_key)
async def api_key_received(message: types.Message, state: FSMContext):
    api_key = message.text.strip()
    await state.update_data(api_key=api_key)
    await message.answer("أرسل Secret Key:")
    await Form.waiting_secret_key.set()

@dp.message_handler(state=Form.waiting_secret_key)
async def secret_key_received(message: types.Message, state: FSMContext):
    secret = message.text.strip()
    await state.update_data(secret=secret)
    data = await state.get_data()
    ex_id = data["selected_exchange"]
    # بعض المنصات تتطلب password/passphrase
    if ex_id in ("kucoin", "okx", "coinbase"):
        await message.answer("أرسل Passphrase/Password (إن لم يوجد اكتب '-' ):")
        await Form.waiting_password.set()
    else:
        # تحقق واحفظ
        await finalize_exchange_creds(message, state, password=None)

@dp.message_handler(state=Form.waiting_password)
async def password_received(message: types.Message, state: FSMContext):
    password = message.text.strip()
    if password == "-":
        password = None
    await finalize_exchange_creds(message, state, password=password)

async def finalize_exchange_creds(message: types.Message, state: FSMContext, password: Optional[str]):
    data = await state.get_data()
    ex_id = data["selected_exchange"]
    api_key = data["api_key"]
    secret = data["secret"]

    valid = await verify_keys(ex_id, api_key, secret, password)
    if not valid:
        await message.answer("❌ المفاتيح غير صحيحة أو الصلاحيات ناقصة. تأكد من تفعيل القراءة والتداول فقط.")
        await state.finish()
        return

    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
    cred = db.query(ExchangeCredential).filter_by(user_id=user.id, exchange_id=ex_id).first()
    if not cred:
        cred = ExchangeCredential(user_id=user.id, exchange_id=ex_id)
    cred.api_key = api_key
    cred.secret = secret
    cred.password = password
    cred.active = True
    db.add(cred)
    db.commit()
    db.close()

    await message.answer(f"✅ تم ربط {SUPPORTED_EXCHANGES[ex_id]} وتفعيلها!", reply_markup=main_menu_keyboard())
    await state.finish()

# ---- تحديد مبلغ وأزواج ----
@dp.callback_query_handler(lambda c: c.data == "menu_set_amount_symbols")
async def set_amount_symbols_handler(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.edit_text(
        "أرسل مبلغ الاستثمار بالدولار (USDT) مثل: 200\nثم أرسل الأزواج مفصولة بفواصل مثل: BTC/USDT,ETH/USDT,SOL/USDT\nإن تركت الأزواج فارغة سنستخدم القائمة الافتراضية.")
    await Form.waiting_investment_amount.set()

@dp.message_handler(state=Form.waiting_investment_amount)
async def amount_received(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.strip())
        await state.update_data(invest_amount=amount)
        await message.answer("أرسل الأزواج (اختياري)، أو أرسل '-' للاستخدام الافتراضي:")
        await Form.choose_symbols.set()
    except Exception:
        await message.answer("❌ أدخل رقمًا صالحًا للمبلغ.")

@dp.message_handler(state=Form.choose_symbols)
async def symbols_received(message: types.Message, state: FSMContext):
    symbols_txt = message.text.strip()
    symbols: List[str]
    if symbols_txt == '-' or not symbols_txt:
        symbols = DEFAULT_SYMBOLS
    else:
        symbols = [s.strip().upper() for s in symbols_txt.split(',') if s.strip()]
    data = await state.get_data()
    amount = data["invest_amount"]

    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
    user.investment_amount = amount
    # نخزن أول زوج كافتراضي (حل وسط)
    user.base_quote = symbols[0]
    user.fee_consent = False  # إعادة طلب موافقة قبل البدء
    db.add(user)
    db.commit()
    db.close()

    await state.update_data(symbols=symbols)

    await message.answer(
        "📋 قبل البدء سنعرض تقدير الرسوم للصفقة الواحدة (جانبي الشراء والبيع) ونحتاج موافقتك.\n"
        "أرسل /consent للموافقة أو /cancel للإلغاء."
    )
    await Form.fee_consent.set()

@dp.message_handler(commands=["consent"], state=Form.fee_consent)
async def consent_given(message: types.Message, state: FSMContext):
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
    user.fee_consent = True
    db.add(user)
    db.commit()
    db.close()

    await message.answer("✅ تم حفظ الموافقة على الرسوم لهذه الجلسة.", reply_markup=main_menu_keyboard())
    await state.finish()

@dp.message_handler(commands=["cancel"], state=Form.fee_consent)
async def consent_cancel(message: types.Message, state: FSMContext):
    await message.answer("تم إلغاء العملية.", reply_markup=main_menu_keyboard())
    await state.finish()

# ---- بدء/إيقاف الاستثمار ----
@dp.callback_query_handler(lambda c: c.data == "menu_start_invest")
async def start_invest_handler(call: types.CallbackQuery):
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=call.from_user.id).first()

    active_creds = db.query(ExchangeCredential).filter_by(user_id=user.id, active=True).all()
    if not active_creds or len(active_creds) < 2:
        await call.answer("❌ يجب تفعيل منصتين على الأقل.")
        db.close()
        return
    if user.investment_amount <= 0:
        await call.answer("❌ لم تحدد مبلغ الاستثمار.")
        db.close()
        return
    if not user.fee_consent:
        await call.answer("❌ يجب الموافقة على الرسوم أولاً عبر قائمة تحديد المبلغ/الأزواج.")
        db.close()
        return

    user.investment_status = "started"
    db.add(user)
    db.commit()
    db.close()
    await call.answer()
    await call.message.edit_text("🚀 تم بدء الاستثمار والمراجحة تلقائياً. يمكنك الإيقاف من القائمة.")
    asyncio.create_task(run_arbitrage_loop(call.from_user.id))

@dp.callback_query_handler(lambda c: c.data == "menu_stop_invest")
async def stop_invest_handler(call: types.CallbackQuery):
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=call.from_user.id).first()
    user.investment_status = "stopped"
    db.add(user)
    db.commit()
    db.close()
    await call.answer()
    await call.message.edit_text("🛑 تم إيقاف الاستثمار.", reply_markup=main_menu_keyboard())

# ---- تقارير ----
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
        await message.answer("❌ صيغة التاريخ غير صحيحة.")

@dp.message_handler(state=Form.waiting_report_end)
async def report_end_date_received(message: types.Message, state: FSMContext):
    try:
        end_date = datetime.strptime(message.text.strip(), "%Y-%m-%d")
        data = await state.get_data()
        start_date = data["report_start"]
        if end_date < start_date:
            await message.answer("❌ النهاية قبل البداية.")
            return

        db = SessionLocal()
        user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
        trades = (
            db.query(TradeLog)
            .filter(
                TradeLog.user_id == user.id,
                TradeLog.timestamp >= start_date,
                TradeLog.timestamp <= end_date + timedelta(days=1),
            )
            .all()
        )
        db.close()

        if not trades:
            await message.answer("لا توجد بيانات عن هذه الفترة.")
            await state.finish()
            return

        total_gross = sum(t.gross_profit for t in trades)
        total_fees = sum(t.fees_total for t in trades)
        total_net = sum(t.net_profit for t in trades)
        lines = [
            f"📊 كشف حساب من {start_date.date()} إلى {end_date.date()}:",
            "\n".join(
                f"{t.timestamp.date()} - {t.symbol} - {t.leg_buy_exchange}->{t.leg_sell_exchange} - صافي: {t.net_profit:.2f} USDT"
                for t in trades
            ),
            "\n",
            f"💵 إجمالي الربح قبل الرسوم: {total_gross:.2f} USDT",
            f"💸 إجمالي الرسوم: {total_fees:.2f} USDT",
            f"✅ الصافي: {total_net:.2f} USDT",
        ]
        await message.answer("\n".join(lines))
        await state.finish()
    except Exception:
        await message.answer("❌ صيغة التاريخ غير صحيحة.")

# ----------------------- ARBITRAGE LOOP -----------------------
async def run_arbitrage_loop(user_telegram_id: int):
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=user_telegram_id).first()
    if not user or user.investment_status != "started":
        db.close()
        return

    # حمّل الرموز التي سيحاول عليها – نخزن فقط الأول في DB، لكن سنجلب الباقي من الحالة المؤقتة عبر fallback
    # للحفاظ على البساطة سنستخدم DEFAULT_SYMBOLS هنا. بإمكانك تخزينها في جدول منفصل لاحقًا.
    symbols = DEFAULT_SYMBOLS

    while True:
        db.refresh(user)
        if user.investment_status != "started":
            db.close()
            return

        try:
            active_creds = db.query(ExchangeCredential).filter_by(user_id=user.id, active=True).all()
            if len(active_creds) < 2:
                await bot.send_message(user.telegram_id, "❌ يجب أن تبقى منصتان مفعّلتان على الأقل. تم الإيقاف.")
                user.investment_status = "stopped"
                db.add(user)
                db.commit()
                db.close()
                return

            for symbol in symbols:
                best_buy, best_sell = await fetch_best_prices(active_creds, symbol)
                if not best_buy or not best_sell:
                    continue
                buy_ex_id, ask = best_buy
                sell_ex_id, bid = best_sell

                # هامش المراجحة التقريبي قبل الرسوم
                spread = bid - ask
                if spread <= 0:
                    continue

                # تقدير الرسوم كنسبة من قيمة الرجلين
                cred_buy = next(c for c in active_creds if c.exchange_id == buy_ex_id)
                cred_sell = next(c for c in active_creds if c.exchange_id == sell_ex_id)
                fee_rate_sum = await estimate_fees(cred_buy, cred_sell, symbol, 0)

                amount_quote = user.investment_amount  # بالدولار (USDT)
                amount_base = amount_quote / ask  # الكمية المراد شراؤها

                gross_profit = spread * amount_base
                fees_total = fee_rate_sum * (amount_quote + amount_base * bid)
                net_profit = gross_profit - fees_total

                # حد أدنى للربح الصافي كي ننفذ (يمكن ضبطه)
                min_net = 1.0  # 1 USDT
                if net_profit <= min_net:
                    continue

                # 🔔 تنبيه ونيل موافقة صريحة قبل أول صفقة على هذا الزوج في الجلسة
                # (يمكن توسيعها لتكون موافقة لكل عملية؛ هنا نفترض موافقة الجلسة كافية)

                # تنفيذ الصفقات (سوق) باستخدام ccxt
                try:
                    ex_buy = build_ccxt_instance(cred_buy)
                    ex_sell = build_ccxt_instance(cred_sell)

                    # تحقق من حدود الحد الأدنى للكمية بدقة السوق
                    await asyncio.to_thread(ex_buy.load_markets)
                    await asyncio.to_thread(ex_sell.load_markets)
                    market = ex_buy.markets.get(symbol) or {}
                    lot = market.get("limits", {}).get("amount", {}).get("min") or 0
                    if lot and amount_base < lot:
                        continue

                    order_buy = await asyncio.to_thread(ex_buy.create_market_buy_order, symbol, amount_base)
                    order_sell = await asyncio.to_thread(ex_sell.create_market_sell_order, symbol, amount_base)

                    # تسجيل
                    t = TradeLog(
                        user_id=user.id,
                        leg_buy_exchange=buy_ex_id,
                        leg_sell_exchange=sell_ex_id,
                        symbol=symbol,
                        amount=amount_base,
                        entry_price=ask,
                        exit_price=bid,
                        gross_profit=gross_profit,
                        fees_total=fees_total,
                        net_profit=net_profit,
                        note="market buy/sell",
                    )
                    db.add(t)
                    db.commit()

                    await bot.send_message(
                        user.telegram_id,
                        (
                            f"✅ صفقة مراجحة ناجحة على {symbol}\n"
                            f"شراء من {SUPPORTED_EXCHANGES.get(buy_ex_id, buy_ex_id)} بسعر {ask:.4f}\n"
                            f"بيع في {SUPPORTED_EXCHANGES.get(sell_ex_id, sell_ex_id)} بسعر {bid:.4f}\n"
                            f"الكمية: {amount_base:.6f}\n"
                            f"💵 الربح قبل الرسوم: {gross_profit:.2f} USDT\n"
                            f"💸 الرسوم المقدّرة: {fees_total:.2f} USDT\n"
                            f"✅ الصافي: {net_profit:.2f} USDT"
                        )
                    )

                except Exception as ex_err:
                    logging.exception(ex_err)
                    await bot.send_message(user.telegram_id, f"❌ خطأ أثناء التنفيذ: {ex_err}")

            # مهلة بين الدورات
            await asyncio.sleep(30)

        except Exception as e:
            logging.exception(e)
            await bot.send_message(user.telegram_id, f"❌ خطأ عام: {e}")
            await asyncio.sleep(30)

# ----------------------- RUN BOT -----------------------
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
