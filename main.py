# bot_main.py
# -*- coding: utf-8 -*-
"""
Triangular Arb Telegram Bot (aiogram 2.25.1)
- إدارة حسابات المستخدم (ربط منصات متعددة) عبر تيليجرام
- تخزين مفاتيح مشفرة في MySQL (Fernet)
- إعداد مبلغ التداول لكل مستخدم
- مسح دورات ثلاثية داخل كل منصة بالتوازي (asyncio + ccxt.async_support)
- تنفيذ صفقات (LIVE_TRADE flag) أو dry-run
- تسجيل الصفقات في جدول trades
Requirements: see requirements.txt
Env needed: see below .env template
"""
import os
import asyncio
import logging
import json
import math
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN

# aiogram 2.25.1
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

# ccxt async
import ccxt.async_support as ccxt

# DB + encryption
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv
from cryptography.fernet import Fernet

# load env
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "")
DATABASE_URL = os.getenv("DATABASE_URL", "")  # e.g. mysql+pymysql://user:pass@host:3306/dbname
# Global defaults (can be overridden per user)
GLOBAL_MIN_PROFIT_PCT = float(os.getenv("MIN_PROFIT_PCT", "0.3"))  # default min profit %
GLOBAL_MAX_SLIPPAGE_PCT = float(os.getenv("MAX_SLIPPAGE_PCT", "0.2"))
GLOBAL_TAKER_FEE_PCT = float(os.getenv("TAKER_FEE_PCT", "0.1"))
GLOBAL_START_SYMBOL = os.getenv("START_SYMBOL", "USDT")
GLOBAL_SCAN_INTERVAL = float(os.getenv("SCAN_INTERVAL", "2.0"))
LIVE_TRADE_DEFAULT = os.getenv("LIVE_TRADE", "false").lower() == "true"

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN missing in env")
if not ENCRYPTION_KEY:
    raise RuntimeError("ENCRYPTION_KEY missing in env")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL missing in env")

fernet = Fernet(ENCRYPTION_KEY)

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

# aiogram init
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher(bot)

# SQLAlchemy sync engine; we'll call DB ops in executor to avoid blocking the event loop
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# In-memory runtime tasks per user to manage scanning loops
user_tasks: Dict[int, asyncio.Task] = {}  # user_id -> asyncio.Task

# ----------------------
# DB schema / migrations (non-destructive)
# ----------------------
def migrate_schema_sync():
    """
    Synchronous migration run at startup. Non-destructive:
    - creates tables users, exchange_accounts, user_settings, trades
    - ensures telegram_chat_id is BIGINT
    """
    schema_statements = [
        # users
        """
        CREATE TABLE IF NOT EXISTS users (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            tg_id BIGINT UNIQUE NOT NULL,
            username VARCHAR(191) NULL,
            created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """,
        # exchange accounts tied to user
        """
        CREATE TABLE IF NOT EXISTS exchange_accounts (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT NOT NULL,
            exchange_id VARCHAR(64) NOT NULL,
            api_key_enc TEXT NOT NULL,
            api_secret_enc TEXT NOT NULL,
            passphrase_enc TEXT NULL,
            testnet TINYINT(1) NOT NULL DEFAULT 0,
            created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_user(user_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """,
        # per-user settings
        """
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id BIGINT PRIMARY KEY,
            trade_amount DECIMAL(36,18) NOT NULL DEFAULT 10,
            min_profit_pct DECIMAL(10,4) NOT NULL DEFAULT 0.3,
            max_slippage_pct DECIMAL(10,4) NOT NULL DEFAULT 0.2,
            live_trade TINYINT(1) NOT NULL DEFAULT 0,
            exchanges_json JSON NULL,
            updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """,
        # trades log
        """
        CREATE TABLE IF NOT EXISTS trades (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT NULL,
            exchange_id VARCHAR(64) NOT NULL,
            cycle_name VARCHAR(191) NOT NULL,
            start_symbol VARCHAR(32) NOT NULL,
            start_amount DECIMAL(36,18) NOT NULL,
            end_amount DECIMAL(36,18) NOT NULL,
            profit_pct DECIMAL(18,8) NOT NULL,
            details_json JSON NULL,
            created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_user(user_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """,
    ]
    with engine.begin() as conn:
        for s in schema_statements:
            conn.execute(text(s))
    logging.info("DB migration done.")


# ----------------------
# Encryption helpers
# ----------------------
def encrypt(text: str) -> str:
    return fernet.encrypt(text.encode()).decode()

def decrypt(token: Optional[str]) -> str:
    if not token:
        return ""
    return fernet.decrypt(token.encode()).decode()

# ----------------------
# DB helpers (run in executor)
# ----------------------
def db_add_user_sync(tg_id: int, username: Optional[str]) -> int:
    with engine.begin() as conn:
        res = conn.execute(text("SELECT id FROM users WHERE tg_id = :tg"), {"tg": tg_id}).fetchone()
        if res:
            return int(res[0])
        r = conn.execute(text("INSERT INTO users(tg_id, username) VALUES (:tg, :u)"), {"tg": tg_id, "u": username})
        return int(r.lastrowid)

def db_get_user_by_tg_sync(tg_id: int):
    with engine.begin() as conn:
        return conn.execute(text("SELECT id, tg_id, username FROM users WHERE tg_id = :tg"), {"tg": tg_id}).fetchone()

def db_set_user_setting_sync(user_id: int, trade_amount: float = None, min_profit_pct: float = None, max_slippage_pct: float = None, live_trade: Optional[int] = None, exchanges_json: Optional[str] = None):
    with engine.begin() as conn:
        # upsert pattern
        cur = conn.execute(text("SELECT user_id FROM user_settings WHERE user_id = :uid"), {"uid": user_id}).fetchone()
        if cur:
            parts = []
            params = {"uid": user_id}
            if trade_amount is not None:
                parts.append("trade_amount = :ta"); params["ta"] = str(Decimal(str(trade_amount)))
            if min_profit_pct is not None:
                parts.append("min_profit_pct = :mp"); params["mp"] = float(min_profit_pct)
            if max_slippage_pct is not None:
                parts.append("max_slippage_pct = :ms"); params["ms"] = float(max_slippage_pct)
            if live_trade is not None:
                parts.append("live_trade = :lt"); params["lt"] = int(live_trade)
            if exchanges_json is not None:
                parts.append("exchanges_json = CAST(:ej AS JSON)"); params["ej"] = exchanges_json
            if parts:
                q = f"UPDATE user_settings SET {', '.join(parts)} WHERE user_id = :uid"
                conn.execute(text(q), params)
        else:
            conn.execute(text("""
                INSERT INTO user_settings(user_id, trade_amount, min_profit_pct, max_slippage_pct, live_trade, exchanges_json)
                VALUES (:uid, :ta, :mp, :ms, :lt, CAST(:ej AS JSON))
            """), {"uid": user_id, "ta": str(Decimal(str(trade_amount or 10))), "mp": float(min_profit_pct or GLOBAL_MIN_PROFIT_PCT), "ms": float(max_slippage_pct or GLOBAL_MAX_SLIPPAGE_PCT), "lt": int(live_trade or 0), "ej": exchanges_json or json.dumps([])})

def db_get_user_setting_sync(user_id: int):
    with engine.begin() as conn:
        r = conn.execute(text("SELECT user_id, trade_amount, min_profit_pct, max_slippage_pct, live_trade, exchanges_json FROM user_settings WHERE user_id = :uid"), {"uid": user_id}).fetchone()
        return r

def db_add_exchange_account_sync(user_id: int, exchange_id: str, api_key: str, api_secret: str, passphrase: str = "", testnet: bool = False):
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO exchange_accounts(user_id, exchange_id, api_key_enc, api_secret_enc, passphrase_enc, testnet)
            VALUES (:uid, :eid, :k, :s, :p, :t)
        """), {"uid": user_id, "eid": exchange_id, "k": encrypt(api_key), "s": encrypt(api_secret), "p": encrypt(passphrase) if passphrase else None, "t": 1 if testnet else 0})

def db_get_exchange_accounts_sync(user_id: int):
    with engine.begin() as conn:
        rows = conn.execute(text("SELECT id, exchange_id, api_key_enc, api_secret_enc, passphrase_enc, testnet FROM exchange_accounts WHERE user_id = :uid"), {"uid": user_id}).fetchall()
        out = []
        for r in rows:
            out.append({
                "id": r[0],
                "exchange_id": r[1],
                "api_key": decrypt(r[2]),
                "api_secret": decrypt(r[3]),
                "passphrase": decrypt(r[4]) if r[4] else "",
                "testnet": bool(r[5])
            })
        return out

def db_log_trade_sync(user_id: int, exchange_id: str, cycle_name: str, start_symbol: str, start_amount: float, end_amount: float, profit_pct: float, details: dict):
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO trades(user_id, exchange_id, cycle_name, start_symbol, start_amount, end_amount, profit_pct, details_json)
            VALUES (:uid, :eid, :cname, :s, :sa, :ea, :p, CAST(:d AS JSON))
        """), {"uid": user_id, "eid": exchange_id, "cname": cycle_name, "s": start_symbol, "sa": str(Decimal(str(start_amount))), "ea": str(Decimal(str(end_amount))), "p": float(profit_pct), "d": json.dumps(details)})

# ----------------------
# Exchange integration helpers
# ----------------------
@dataclass
class Leg:
    symbol: str
    side: str

@dataclass
class Cycle:
    name: str
    legs: List[Leg]

@dataclass
class XCtx:
    id: str
    client: ccxt.Exchange
    markets: dict
    taker_fee_pct: float

async def make_exchange_ctx(ex_id: str, api_key: Optional[str], api_secret: Optional[str], passphrase: Optional[str], testnet: bool) -> XCtx:
    params = {"enableRateLimit": True, "options": {"defaultType": "spot", "adjustForTimeDifference": True}}
    ex_id_lower = ex_id.lower()
    if ex_id_lower == "binance":
        params.update({"apiKey": api_key or "", "secret": api_secret or ""})
        ex = ccxt.binance(params)
        if testnet:
            ex.set_sandbox_mode(True)
    elif ex_id_lower == "kucoin":
        params.update({"apiKey": api_key or "", "secret": api_secret or "", "password": passphrase or ""})
        ex = ccxt.kucoin(params)
        if testnet:
            ex.set_sandbox_mode(True)
    elif ex_id_lower == "bitget":
        params.update({"apiKey": api_key or "", "secret": api_secret or "", "password": passphrase or ""})
        ex = ccxt.bitget(params)
        if testnet:
            ex.set_sandbox_mode(True)
    else:
        # generic ccxt
        cls = getattr(ccxt, ex_id_lower)
        ex = cls(params)
    markets = await ex.load_markets()
    # try fetch taker fee
    tak = GLOBAL_TAKER_FEE_PCT
    try:
        if hasattr(ex, "fees") and isinstance(ex.fees, dict):
            t = ex.fees.get("trading", {}).get("taker")
            if t is not None:
                tak = float(t) * 100.0 if t < 1 else float(t)
    except Exception:
        pass
    return XCtx(id=ex_id_lower, client=ex, markets=markets, taker_fee_pct=tak)

async def best_bid_ask(ctx: XCtx, symbol: str):
    ob = await ctx.client.fetch_order_book(symbol, limit=5)
    bid = ob["bids"][0][0] if ob["bids"] else None
    ask = ob["asks"][0][0] if ob["asks"] else None
    return bid, ask

async def simulate_cycle(ctx: XCtx, cycle: Cycle, start_amount: float, max_slippage_pct: float):
    amt = start_amount
    for leg in cycle.legs:
        bid, ask = await best_bid_ask(ctx, leg.symbol)
        if bid is None or ask is None:
            return float("nan")
        if leg.side == "buy":
            price = ask * (1 + max_slippage_pct / 100.0)
            base_received = amt / price
            amt = base_received * (1 - ctx.taker_fee_pct / 100.0)
        else:
            price = bid * (1 - max_slippage_pct / 100.0)
            quote_received = amt * price
            amt = quote_received * (1 - ctx.taker_fee_pct / 100.0)
    return amt

def generate_cycles_from_markets(markets: dict, start_quote: str) -> List[Cycle]:
    by_quote = {}
    symbols = [s for s, m in markets.items() if m.get("spot") and "/" in s]
    for s in symbols:
        base, quote = s.split("/")
        by_quote.setdefault(quote, set()).add(base)
    bases = list(by_quote.get(start_quote, set()))
    cycles = []
    symbols_set = set(symbols)
    for a in bases:
        for b in bases:
            if a == b:
                continue
            s1 = f"{a}/{start_quote}"
            s2 = f"{b}/{a}"
            s3 = f"{b}/{start_quote}"
            if s1 in symbols_set and s2 in symbols_set and s3 in symbols_set:
                cycles.append(Cycle(name=f"{start_quote}-{a}-{b}", legs=[
                    Leg(symbol=s1, side="buy"),
                    Leg(symbol=s2, side="buy"),
                    Leg(symbol=s3, side="sell"),
                ]))
    return cycles

async def place_market_order(ctx: XCtx, symbol: str, side: str, amount_base: float, quote_order_qty: float = None):
    params = {}
    try:
        if quote_order_qty is not None:
            params["quoteOrderQty"] = await ctx.client.cost_to_precision(symbol, quote_order_qty)
            return await ctx.client.create_order(symbol, "market", side, 0, None, params)
    except Exception:
        pass
    amt_prec = await ctx.client.amount_to_precision(symbol, amount_base)
    return await ctx.client.create_order(symbol, "market", side, float(amt_prec))

async def execute_cycle_live(ctx: XCtx, cycle: Cycle, trade_amount: float, max_slippage_pct: float, start_symbol: str):
    # Note: simple execution flow (market taker orders). Real world needs more checks.
    # Leg 1: spend start_symbol to buy A (quoteOrderQty)
    leg1 = cycle.legs[0]
    if leg1.side != "buy":
        raise ValueError("Leg1 must be buy")
    await place_market_order(ctx, leg1.symbol, "buy", amount_base=0, quote_order_qty=trade_amount)
    await asyncio.sleep(0.2)
    base1 = leg1.symbol.split("/")[0]
    bal = await ctx.client.fetch_free_balance()
    amt_base1 = float(bal.get(base1, 0.0))

    # Leg2: buy B using A
    leg2 = cycle.legs[1]
    spend_a = amt_base1 * (1 - max_slippage_pct / 100.0)
    await place_market_order(ctx, leg2.symbol, "buy", amount_base=0, quote_order_qty=spend_a)
    await asyncio.sleep(0.2)
    base2 = leg2.symbol.split("/")[0]
    bal2 = await ctx.client.fetch_free_balance()
    amt_base2 = float(bal2.get(base2, 0.0))

    # Leg3: sell B to START
    leg3 = cycle.legs[2]
    sell_amt = amt_base2 * (1 - max_slippage_pct / 100.0)
    await place_market_order(ctx, leg3.symbol, "sell", amount_base=sell_amt)
    await asyncio.sleep(0.4)
    final_bal = await ctx.client.fetch_free_balance()
    return float(final_bal.get(start_symbol, 0.0))

# ----------------------
# Scanning loop per user
# ----------------------
async def user_scan_loop(user_id: int):
    """
    For a single user: load his settings & exchange accounts, create per-exchange ctxs,
    and run parallel scan per exchange. This function keeps running until cancelled.
    """
    logging.info(f"[user_scan_loop] start for user {user_id}")
    try:
        # load settings & accounts (sync DB calls via run_in_executor)
        loop = asyncio.get_event_loop()
        settings_row = await loop.run_in_executor(None, db_get_user_setting_sync, user_id)
        if not settings_row:
            logging.info(f"[user_scan_loop] no settings for user {user_id}, using defaults")
            trade_amount = TRADE_AMOUNT_DEFAULT = 10.0
            min_profit = GLOBAL_MIN_PROFIT_PCT
            max_slippage = GLOBAL_MAX_SLIPPAGE_PCT
            live_trade = LIVE_TRADE_DEFAULT
            exchanges_list = []
        else:
            trade_amount = float(settings_row[1])
            min_profit = float(settings_row[2])
            max_slippage = float(settings_row[3])
            live_trade = bool(int(settings_row[4]))
            exchanges_list = json.loads(settings_row[5]) if settings_row[5] else []

        # load accounts
        accounts = await loop.run_in_executor(None, db_get_exchange_accounts_sync, user_id)
        # build ctx per account (we only start for accounts in user's exchanges_list)
        ctxs = []
        for acc in accounts:
            if exchanges_list and acc["exchange_id"] not in exchanges_list:
                continue
            try:
                ctx = await make_exchange_ctx(acc["exchange_id"], acc["api_key"], acc["api_secret"], acc["passphrase"], acc["testnet"])
                ctxs.append(ctx)
            except Exception as e:
                logging.error(f"[user_scan_loop] failed to init exchange {acc['exchange_id']} for user {user_id}: {e}")

        if not ctxs:
            logging.info(f"[user_scan_loop] no exchange contexts for user {user_id}. Exiting loop.")
            return

        # generate cycles per ctx and scan in parallel
        start_symbol = GLOBAL_START_SYMBOL
        # pre-generate cycles per ctx
        ctx_cycles = []
        for ctx in ctxs:
            cycles = generate_cycles_from_markets(ctx.markets, start_symbol)
            logging.info(f"[user_scan_loop] user {user_id} exchange {ctx.id} cycles {len(cycles)}")
            if cycles:
                ctx_cycles.append((ctx, cycles))

        if not ctx_cycles:
            logging.info(f"[user_scan_loop] no cycles for any exchange (user {user_id})")
            return

        # continuous scanning
        while True:
            # for each exchange, run all cycle simulations concurrently per exchange (gather)
            exch_tasks = []
            for ctx, cycles in ctx_cycles:
                # simulate all cycles concurrently for this ctx
                tasks = [simulate_cycle(ctx, c, trade_amount, max_slippage) for c in cycles]
                exch_tasks.append((ctx, cycles, asyncio.gather(*tasks, return_exceptions=True)))
            # await all gathers
            results_per_exchange = []
            for ctx, cycles, gather_task in exch_tasks:
                res = await gather_task
                results_per_exchange.append((ctx, cycles, res))

            # evaluate best per exchange and potentially execute
            for ctx, cycles, res in results_per_exchange:
                best = None
                for c, out in zip(cycles, res):
                    if isinstance(out, Exception) or math.isnan(out):
                        continue
                    profit_pct = (out - trade_amount) / trade_amount * 100.0
                    if best is None or profit_pct > best[1]:
                        best = (c, profit_pct, out)
                if best and best[1] >= min_profit:
                    cycle, p, est_out = best
                    msg = f"[user {user_id}] ✨ Opportunity on {ctx.id} {cycle.name}: ~{p:.3f}% > {min_profit}% (amt {trade_amount} {start_symbol})"
                    logging.info(msg)
                    try:
                        await bot.send_message(user_id, msg)
                    except Exception:
                        logging.debug("Cannot send tg message to user (maybe blocked).")

                    # execute or dry-run
                    if live_trade:
                        try:
                            final_q = await execute_cycle_live(ctx, cycle, trade_amount, max_slippage, start_symbol)
                        except Exception as e:
                            logging.error(f"[user_scan_loop] execution failed: {e}")
                            final_q = est_out
                    else:
                        final_q = est_out

                    pnl_abs = final_q - trade_amount
                    # log trade in DB
                    await asyncio.get_event_loop().run_in_executor(None, db_log_trade_sync, user_id, ctx.id, cycle.name, start_symbol, trade_amount, final_q, float(p), {"est": est_out, "live": live_trade})
                    done_msg = f"[user {user_id}] Done {ctx.id} {cycle.name} | start={trade_amount:.6f} end={final_q:.6f} pnl={pnl_abs:.6f} {start_symbol}"
                    logging.info(done_msg)
                    try:
                        await bot.send_message(user_id, done_msg)
                    except Exception:
                        pass
            await asyncio.sleep(GLOBAL_SCAN_INTERVAL)
    except asyncio.CancelledError:
        logging.info(f"user_scan_loop {user_id} cancelled")
    except Exception as e:
        logging.exception(f"user_scan_loop error for {user_id}: {e}")

# ----------------------
# aiogram handlers / menu
# ----------------------
# Simple reply keyboard
main_kb = ReplyKeyboardMarkup(resize_keyboard=True)
main_kb.add(KeyboardButton("🔗 ربط منصة جديدة"))
main_kb.add(KeyboardButton("💰 تعيين مبلغ التداول"))
main_kb.add(KeyboardButton("▶️ تشغيل/ايقاف التداول"))
main_kb.add(KeyboardButton("📈 عرض الصفقات"))
main_kb.add(KeyboardButton("🛠️ إعدادات"))

# stateful input flags (simple approach)
pending_add_exchange = {}  # tg_id -> step info
pending_set_amount = {}  # tg_id -> awaiting value

@dp.message_handler(commands=["start", "help"])
async def cmd_start(msg: types.Message):
    # register user in DB
    uid = await asyncio.get_event_loop().run_in_executor(None, db_add_user_sync, msg.from_user.id, msg.from_user.username)
    await msg.answer("أهلاً! أضفت حسابك. استخدم القائمة لاختيار إجراء.", reply_markup=main_kb)

@dp.message_handler(lambda m: m.text == "🔗 ربط منصة جديدة")
async def cmd_add_exchange(msg: types.Message):
    await msg.answer("ادخل اسم المنصة (مثال: binance, kucoin, bitget):", reply_markup=ReplyKeyboardRemove())
    pending_add_exchange[msg.from_user.id] = {"step": "ask_name"}
@dp.message_handler(lambda m: m.from_user.id in pending_add_exchange and pending_add_exchange[m.from_user.id]["step"] == "ask_name")
async def handle_add_name(msg: types.Message):
    tg = msg.from_user.id
    name = msg.text.strip().lower()
    pending_add_exchange[tg].update({"exchange_id": name, "step": "ask_key"})
    await msg.answer("ادخل API Key (أرسل 'إلغاء' لإلغاء):")
@dp.message_handler(lambda m: m.from_user.id in pending_add_exchange and pending_add_exchange[m.from_user.id]["step"] == "ask_key")
async def handle_add_key(msg: types.Message):
    tg = msg.from_user.id
    if msg.text.strip().lower() == "إلغاء":
        pending_add_exchange.pop(tg, None)
        await msg.answer("تم الإلغاء.", reply_markup=main_kb)
        return
    pending_add_exchange[tg].update({"api_key": msg.text.strip(), "step": "ask_secret"})
    await msg.answer("ادخل API Secret:")
@dp.message_handler(lambda m: m.from_user.id in pending_add_exchange and pending_add_exchange[m.from_user.id]["step"] == "ask_secret")
async def handle_add_secret(msg: types.Message):
    tg = msg.from_user.id
    pending_add_exchange[tg].update({"api_secret": msg.text.strip(), "step": "ask_pass"})
    await msg.answer("ادخل passphrase (او اكتب '-' اذا مفيش):")
@dp.message_handler(lambda m: m.from_user.id in pending_add_exchange and pending_add_exchange[m.from_user.id]["step"] == "ask_pass")
async def handle_add_pass(msg: types.Message):
    tg = msg.from_user.id
    data = pending_add_exchange.pop(tg)
    passphrase = "" if msg.text.strip() == "-" else msg.text.strip()
    # store in db
    await asyncio.get_event_loop().run_in_executor(None, db_add_exchange_account_sync, await asyncio.get_event_loop().run_in_executor(None, db_get_user_by_tg_sync, tg)[0], data["exchange_id"], data["api_key"], data["api_secret"], passphrase, False)
    await msg.answer(f"تم إضافة الحساب على {data['exchange_id']}.", reply_markup=main_kb)

@dp.message_handler(lambda m: m.text == "💰 تعيين مبلغ التداول")
async def cmd_set_amount(msg: types.Message):
    await msg.answer("اكتب مبلغ التداول بالـ USDT (مثال: 10):", reply_markup=ReplyKeyboardRemove())
    pending_set_amount[msg.from_user.id] = True

@dp.message_handler(lambda m: m.from_user.id in pending_set_amount)
async def handle_amount(msg: types.Message):
    tg = msg.from_user.id
    try:
        val = float(msg.text.strip())
        # upsert setting
        user_row = await asyncio.get_event_loop().run_in_executor(None, db_get_user_by_tg_sync, tg)
        user_id = int(user_row[0])
        await asyncio.get_event_loop().run_in_executor(None, db_set_user_setting_sync, user_id, val, None, None, None, None)
        pending_set_amount.pop(tg, None)
        await msg.answer(f"تم حفظ مبلغ التداول = {val} USDT", reply_markup=main_kb)
    except Exception:
        await msg.answer("القيمة غير صحيحة. اكتب رقم مثل: 10")

@dp.message_handler(lambda m: m.text == "▶️ تشغيل/ايقاف التداول")
async def cmd_toggle_running(msg: types.Message):
    tg = msg.from_user.id
    # ensure user exists
    user_row = await asyncio.get_event_loop().run_in_executor(None, db_get_user_by_tg_sync, tg)
    if not user_row:
        await msg.answer("سجّل أولًا بـ /start", reply_markup=main_kb)
        return
    user_id = int(user_row[0])
    # read current setting
    settings = await asyncio.get_event_loop().run_in_executor(None, db_get_user_setting_sync, user_id)
    currently = bool(int(settings[4])) if settings else False
    if currently:
        # stop
        # cancel task if running
        t = user_tasks.get(user_id)
        if t:
            t.cancel()
            user_tasks.pop(user_id, None)
        await asyncio.get_event_loop().run_in_executor(None, db_set_user_setting_sync, user_id, None, None, None, 0, None)
        await msg.answer("تم إيقاف التداول.", reply_markup=main_kb)
    else:
        # start: ensure settings exist
        if not settings:
            await asyncio.get_event_loop().run_in_executor(None, db_set_user_setting_sync, user_id, 10.0, GLOBAL_MIN_PROFIT_PCT, GLOBAL_MAX_SLIPPAGE_PCT, 1, json.dumps([]))
        else:
            await asyncio.get_event_loop().run_in_executor(None, db_set_user_setting_sync, user_id, None, None, None, 1, None)
        # spawn background scan loop for user
        task = asyncio.create_task(user_scan_loop(user_id))
        user_tasks[user_id] = task
        await msg.answer("التداول شغّال الآن (في الخلفية).", reply_markup=main_kb)

@dp.message_handler(lambda m: m.text == "📈 عرض الصفقات")
async def cmd_show_trades(msg: types.Message):
    tg = msg.from_user.id
    u = await asyncio.get_event_loop().run_in_executor(None, db_get_user_by_tg_sync, tg)
    if not u:
        await msg.answer("سجّل أولًا بالـ /start", reply_markup=main_kb); return
    uid = int(u[0])
    with engine.begin() as conn:
        rows = conn.execute(text("SELECT exchange_id, cycle_name, start_amount, end_amount, profit_pct, created_at FROM trades WHERE user_id = :uid ORDER BY id DESC LIMIT 20"), {"uid": uid}).fetchall()
    if not rows:
        await msg.answer("لا توجد صفقات بعد.", reply_markup=main_kb); return
    text_lines = ["آخر الصفقات:"]
    for r in rows:
        text_lines.append(f"{r[5]} | {r[0]} | {r[1]} | start={r[2]} end={r[3]} pnl%={r[4]}")
    await msg.answer("\n".join(text_lines), reply_markup=main_kb)

@dp.message_handler(lambda m: m.text == "🛠️ إعدادات")
async def cmd_settings(msg: types.Message):
    tg = msg.from_user.id
    u = await asyncio.get_event_loop().run_in_executor(None, db_get_user_by_tg_sync, tg)
    if not u:
        await msg.answer("سجّل أولًا بـ /start", reply_markup=main_kb); return
    uid = int(u[0])
    s = await asyncio.get_event_loop().run_in_executor(None, db_get_user_setting_sync, uid)
    if not s:
        await msg.answer("لم تُعدّ إعدادات بعد. استخدم القائمة.", reply_markup=main_kb); return
    exchanges = json.loads(s[5]) if s[5] else []
    await msg.answer(f"مبلغ تداول: {s[1]} USDT\nmin profit%: {s[2]}\nslippage%: {s[3]}\nlive trade: {bool(int(s[4]))}\nالمنصات المفعّلة: {exchanges}", reply_markup=main_kb)

# ----------------------
# Startup / shutdown
# ----------------------
def start_background_scan_for_all_running_users():
    # find users with live_trade = 1 and spawn tasks
    with engine.begin() as conn:
        rows = conn.execute(text("SELECT user_id FROM user_settings WHERE live_trade = 1")).fetchall()
    loop = asyncio.get_event_loop()
    for r in rows:
        uid = int(r[0])
        if uid not in user_tasks:
            user_tasks[uid] = loop.create_task(user_scan_loop(uid))
            logging.info(f"Spawned background scan for user {uid}")

async def on_startup(dp):
    # migrate DB
    await asyncio.get_event_loop().run_in_executor(None, migrate_schema_sync)
    # spawn background tasks for any running users
    await asyncio.get_event_loop().run_in_executor(None, start_background_scan_for_all_running_users)
    logging.info("Bot started.")

async def on_shutdown(dp):
    # cancel background tasks
    for t in list(user_tasks.values()):
        t.cancel()
    # close aiogram bot
    await bot.close()
    logging.info("Bot stopped.")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup, on_shutdown=on_shutdown)
