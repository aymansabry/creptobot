# arb_bot_full.py
# -*- coding: utf-8 -*-
"""
Triangular + Cross-Exchange Arbitrage Bot
- Aiogram 2.25.1 bot UI to manage user accounts & exchange API keys (encrypted).
- MySQL storage for users, exchange_accounts, user_settings, trades.
- Background asyncio tasks scanning:
    * Triangular arbitrage inside each exchange (full cycles generation).
    * Cross-exchange price gap checks between user's linked exchanges (same symbol).
- Each user works with their own API keys and trade_amount.
- Uses ccxt.async_support for exchange interaction.
- Use DRY-RUN default; enable LIVE_TRADE in user settings to execute.
"""
import os
import json
import math
import asyncio
import logging
from decimal import Decimal, ROUND_DOWN
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple, Set

import ccxt.async_support as ccxt
from dotenv import load_dotenv
from cryptography.fernet import Fernet
from sqlalchemy import create_engine, text
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

load_dotenv()
# -------------------------
# Env
# -------------------------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
DATABASE_URL = os.getenv("DATABASE_URL", "")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "")

GLOBAL_START_SYMBOL = os.getenv("GLOBAL_START_SYMBOL", "USDT").upper()
GLOBAL_MIN_PROFIT_PCT = float(os.getenv("GLOBAL_MIN_PROFIT_PCT", "0.3"))
GLOBAL_MAX_SLIPPAGE_PCT = float(os.getenv("GLOBAL_MAX_SLIPPAGE_PCT", "0.2"))
GLOBAL_SCAN_INTERVAL = float(os.getenv("GLOBAL_SCAN_INTERVAL", "2.0"))
LIVE_TRADE_DEFAULT = os.getenv("LIVE_TRADE", "false").lower() == "true"

if not TELEGRAM_BOT_TOKEN or not DATABASE_URL or not ENCRYPTION_KEY:
    raise RuntimeError("Set TELEGRAM_BOT_TOKEN, DATABASE_URL and ENCRYPTION_KEY in .env")

fernet = Fernet(ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY)

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

# aiogram init
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher(bot)

# DB engine (sync access via run_in_executor)
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# in-memory tasks per user
user_tasks: Dict[int, asyncio.Task] = {}

# -------------------------
# DB migrations (sync)
# -------------------------
def migrate_sync():
    stmts = [
    """
    CREATE TABLE IF NOT EXISTS users (
        id BIGINT AUTO_INCREMENT PRIMARY KEY,
        tg_id BIGINT UNIQUE NOT NULL,
        username VARCHAR(191) NULL,
        created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
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
    """
    ]
    with engine.begin() as conn:
        for s in stmts:
            conn.execute(text(s))
    logging.info("DB migration done.")

# -------------------------
# encryption helpers
# -------------------------
def enc(s: str) -> str:
    return fernet.encrypt(s.encode()).decode()

def dec(s: Optional[str]) -> str:
    if not s:
        return ""
    return fernet.decrypt(s.encode()).decode()

# -------------------------
# DB CRUD (sync) — called via run_in_executor
# -------------------------
def db_add_user_sync(tg_id: int, username: Optional[str]) -> int:
    with engine.begin() as conn:
        r = conn.execute(text("SELECT id FROM users WHERE tg_id = :tg"), {"tg": tg_id}).fetchone()
        if r:
            return int(r[0])
        res = conn.execute(text("INSERT INTO users(tg_id, username) VALUES (:tg, :u)"), {"tg": tg_id, "u": username})
        return int(res.lastrowid)

def db_get_user_by_tg_sync(tg_id: int):
    with engine.begin() as conn:
        return conn.execute(text("SELECT id, tg_id, username FROM users WHERE tg_id = :tg"), {"tg": tg_id}).fetchone()

def db_set_user_setting_sync(user_id: int, trade_amount: Optional[float]=None, min_profit_pct: Optional[float]=None, max_slippage_pct: Optional[float]=None, live_trade: Optional[int]=None, exchanges_json: Optional[str]=None):
    with engine.begin() as conn:
        cur = conn.execute(text("SELECT user_id FROM user_settings WHERE user_id = :uid"), {"uid": user_id}).fetchone()
        if cur:
            parts=[]; params={"uid": user_id}
            if trade_amount is not None: parts.append("trade_amount=:ta"); params["ta"]=str(Decimal(str(trade_amount)))
            if min_profit_pct is not None: parts.append("min_profit_pct=:mp"); params["mp"]=float(min_profit_pct)
            if max_slippage_pct is not None: parts.append("max_slippage_pct=:ms"); params["ms"]=float(max_slippage_pct)
            if live_trade is not None: parts.append("live_trade=:lt"); params["lt"]=int(live_trade)
            if exchanges_json is not None: parts.append("exchanges_json=CAST(:ej AS JSON)"); params["ej"]=exchanges_json
            if parts:
                conn.execute(text(f"UPDATE user_settings SET {','.join(parts)} WHERE user_id = :uid"), params)
        else:
            conn.execute(text("""
                INSERT INTO user_settings(user_id, trade_amount, min_profit_pct, max_slippage_pct, live_trade, exchanges_json)
                VALUES (:uid, :ta, :mp, :ms, :lt, CAST(:ej AS JSON))
            """), {"uid": user_id, "ta": str(Decimal(str(trade_amount or 10))), "mp": float(min_profit_pct or GLOBAL_MIN_PROFIT_PCT), "ms": float(max_slippage_pct or GLOBAL_MAX_SLIPPAGE_PCT), "lt": int(live_trade or 0), "ej": exchanges_json or json.dumps([])})

def db_get_user_setting_sync(user_id: int):
    with engine.begin() as conn:
        return conn.execute(text("SELECT user_id, trade_amount, min_profit_pct, max_slippage_pct, live_trade, exchanges_json FROM user_settings WHERE user_id = :uid"), {"uid": user_id}).fetchone()

def db_add_exchange_account_sync(user_id: int, exchange_id: str, api_key: str, api_secret: str, passphrase: str, testnet: bool=False):
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO exchange_accounts(user_id, exchange_id, api_key_enc, api_secret_enc, passphrase_enc, testnet)
            VALUES (:uid, :eid, :k, :s, :p, :t)
        """), {"uid": user_id, "eid": exchange_id, "k": enc(api_key), "s": enc(api_secret), "p": enc(passphrase) if passphrase else None, "t": 1 if testnet else 0})

def db_get_exchange_accounts_sync(user_id: int):
    with engine.begin() as conn:
        rows = conn.execute(text("SELECT id, exchange_id, api_key_enc, api_secret_enc, passphrase_enc, testnet FROM exchange_accounts WHERE user_id = :uid"), {"uid": user_id}).fetchall()
        out=[]
        for r in rows:
            out.append({"id": r[0], "exchange_id": r[1], "api_key": dec(r[2]), "api_secret": dec(r[3]), "passphrase": dec(r[4]) if r[4] else "", "testnet": bool(r[5])})
        return out

def db_log_trade_sync(user_id: int, exchange_id: str, cycle_name: str, start_symbol: str, start_amount: float, end_amount: float, profit_pct: float, details: dict):
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO trades(user_id, exchange_id, cycle_name, start_symbol, start_amount, end_amount, profit_pct, details_json)
            VALUES (:uid, :eid, :c, :s, :sa, :ea, :p, CAST(:d AS JSON))
        """), {"uid": user_id, "eid": exchange_id, "c": cycle_name, "s": start_symbol, "sa": str(Decimal(str(start_amount))), "ea": str(Decimal(str(end_amount))), "p": float(profit_pct), "d": json.dumps(details)})

# -------------------------
# Exchange helpers (async)
# -------------------------
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

async def make_exchange_ctx(ex_id: str, api_key: str, api_secret: str, passphrase: str, testnet: bool) -> XCtx:
    params = {"enableRateLimit": True, "options": {"defaultType": "spot", "adjustForTimeDifference": True}}
    cl = None
    ex = ex_id.lower()
    if ex == "binance":
        params.update({"apiKey": api_key or "", "secret": api_secret or ""})
        cl = ccxt.binance(params)
        if testnet: cl.set_sandbox_mode(True)
    elif ex == "kucoin":
        params.update({"apiKey": api_key or "", "secret": api_secret or "", "password": passphrase or ""})
        cl = ccxt.kucoin(params)
        if testnet: cl.set_sandbox_mode(True)
    elif ex == "bitget":
        params.update({"apiKey": api_key or "", "secret": api_secret or "", "password": passphrase or ""})
        cl = ccxt.bitget(params)
        if testnet: cl.set_sandbox_mode(True)
    else:
        if hasattr(ccxt, ex):
            cls = getattr(ccxt, ex)
            cl = cls(params)
        else:
            raise RuntimeError(f"Unknown exchange {ex_id}")
    markets = await cl.load_markets()
    tak = GLOBAL_MAX_SLIPPAGE_PCT  # fallback
    try:
        fees = getattr(cl, "fees", None)
        if fees and isinstance(fees, dict):
            t = fees.get("trading", {}).get("taker")
            if t is not None:
                tak = float(t)*100.0 if t < 1 else float(t)
    except Exception:
        pass
    return XCtx(id=ex, client=cl, markets=markets, taker_fee_pct=tak)

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
            price = ask * (1 + max_slippage_pct/100.0)
            base_received = amt / price
            amt = base_received * (1 - ctx.taker_fee_pct/100.0)
        else:
            price = bid * (1 - max_slippage_pct/100.0)
            quote_received = amt * price
            amt = quote_received * (1 - ctx.taker_fee_pct/100.0)
    return amt

def generate_triangular_cycles(markets: dict, start_quote: str) -> List[Cycle]:
    by_quote: Dict[str, Set[str]] = {}
    symbols = [s for s, m in markets.items() if m.get("spot") and "/" in s]
    for s in symbols:
        base, quote = s.split("/")
        by_quote.setdefault(quote, set()).add(base)
    bases = list(by_quote.get(start_quote, set()))
    cycles=[]
    sset = set(symbols)
    for a in bases:
        for b in bases:
            if a==b: continue
            s1 = f"{a}/{start_quote}"
            s2 = f"{b}/{a}"
            s3 = f"{b}/{start_quote}"
            if s1 in sset and s2 in sset and s3 in sset:
                cycles.append(Cycle(name=f"{start_quote}-{a}-{b}", legs=[Leg(symbol=s1, side="buy"), Leg(symbol=s2, side="buy"), Leg(symbol=s3, side="sell")] ))
    return cycles

# Cross-exchange simple comparator for same symbol
async def check_cross_exchange_simple(ctxs: List[XCtx], symbol: str, start_amount: float):
    # fetch top asks/bids across ctxs
    quotes=[]
    for ctx in ctxs:
        try:
            bid, ask = await best_bid_ask(ctx, symbol)
            if bid and ask:
                quotes.append({"ctx": ctx, "bid": bid, "ask": ask})
        except Exception:
            continue
    if len(quotes) < 2:
        return None
    # find lowest ask and highest bid
    lowest = min(quotes, key=lambda x: x["ask"])
    highest = max(quotes, key=lambda x: x["bid"])
    # profit if highest.bid > lowest.ask after fees and slippage
    buy_price = lowest["ask"] * (1 + GLOBAL_MAX_SLIPPAGE_PCT/100.0)
    sell_price = highest["bid"] * (1 - GLOBAL_MAX_SLIPPAGE_PCT/100.0)
    # consider taker fees approx avg
    buy_fee = lowest["ctx"].taker_fee_pct/100.0
    sell_fee = highest["ctx"].taker_fee_pct/100.0
    base_qty = start_amount / buy_price
    proceeds = base_qty * sell_price * (1 - sell_fee)
    cost = start_amount * (1 + buy_fee)
    profit_pct = (proceeds - cost) / cost * 100.0
    return {"buy_ctx": lowest["ctx"], "sell_ctx": highest["ctx"], "profit_pct": profit_pct, "buy_price": lowest["ask"], "sell_price": highest["bid"], "est_out": proceeds}

# Execution (simple market taker)
async def place_market_order(ctx: XCtx, symbol: str, side: str, amount_base: float=None, quote_order_qty: float=None):
    params={}
    try:
        if quote_order_qty is not None:
            params["quoteOrderQty"] = quote_order_qty
            return await ctx.client.create_order(symbol, "market", side, 0, None, params)
    except Exception:
        pass
    amt_prec = amount_base
    return await ctx.client.create_order(symbol, "market", side, float(amt_prec))

async def execute_tri_cycle_live(ctx: XCtx, cycle: Cycle, trade_amount: float, max_slippage_pct: float, start_symbol: str):
    leg1 = cycle.legs[0]
    await place_market_order(ctx, leg1.symbol, "buy", quote_order_qty=trade_amount)
    await asyncio.sleep(0.2)
    base1 = leg1.symbol.split("/")[0]
    bal = await ctx.client.fetch_free_balance()
    amt_base1 = float(bal.get(base1,0.0))
    leg2 = cycle.legs[1]
    spend_a = amt_base1 * (1 - max_slippage_pct/100.0)
    await place_market_order(ctx, leg2.symbol, "buy", quote_order_qty=spend_a)
    await asyncio.sleep(0.2)
    base2 = leg2.symbol.split("/")[0]
    bal2 = await ctx.client.fetch_free_balance()
    amt_base2 = float(bal2.get(base2,0.0))
    leg3 = cycle.legs[2]
    sell_amt = amt_base2 * (1 - max_slippage_pct/100.0)
    await place_market_order(ctx, leg3.symbol, "sell", amount_base=sell_amt)
    await asyncio.sleep(0.4)
    final_bal = await ctx.client.fetch_free_balance()
    return float(final_bal.get(start_symbol,0.0))

# -------------------------
# User background scanner (task)
# -------------------------
async def user_scan_loop(user_id: int):
    logging.info(f"Starting scan loop for user {user_id}")
    loop = asyncio.get_event_loop()
    # load settings & accounts
    settings_row = await loop.run_in_executor(None, db_get_user_setting_sync, user_id)
    if not settings_row:
        # defaults
        trade_amount = 10.0
        min_profit = GLOBAL_MIN_PROFIT_PCT
        max_slip = GLOBAL_MAX_SLIPPAGE_PCT
        live_trade = LIVE_TRADE_DEFAULT
        exchanges_enabled = []
    else:
        trade_amount = float(settings_row[1])
        min_profit = float(settings_row[2])
        max_slip = float(settings_row[3])
        live_trade = bool(int(settings_row[4]))
        exchanges_enabled = json.loads(settings_row[5]) if settings_row[5] else []

    accounts = await loop.run_in_executor(None, db_get_exchange_accounts_sync, user_id)
    # build ctxs for accounts enabled
    ctxs=[]
    for acc in accounts:
        if exchanges_enabled and acc["exchange_id"] not in exchanges_enabled:
            continue
        try:
            ctx = await make_exchange_ctx(acc["exchange_id"], acc["api_key"], acc["api_secret"], acc["passphrase"], acc["testnet"])
            ctxs.append(ctx)
        except Exception as e:
            logging.error(f"Failed to init ctx {acc['exchange_id']} user {user_id}: {e}")
    if not ctxs:
        logging.info(f"No exchange contexts for user {user_id}; exiting scan loop")
        return

    # per-ctx generate cycles
    ctx_cycles=[]
    for ctx in ctxs:
        cycles = generate_triangular_cycles(ctx.markets, GLOBAL_START_SYMBOL)
        logging.info(f"user {user_id} ctx {ctx.id} cycles {len(cycles)}")
        ctx_cycles.append((ctx, cycles))

    # continuous scanning
    while True:
        try:
            # Triangular: for each ctx simulate cycles in parallel
            for ctx, cycles in ctx_cycles:
                if not cycles: continue
                sim_tasks = [simulate_cycle(ctx, c, trade_amount, max_slip) for c in cycles]
                results = await asyncio.gather(*sim_tasks, return_exceptions=True)
                best=None
                for c, out in zip(cycles, results):
                    if isinstance(out, Exception) or math.isnan(out): continue
                    profit_pct = (out - trade_amount)/trade_amount*100.0
                    if best is None or profit_pct>best[1]:
                        best=(c, profit_pct, out)
                if best and best[1] >= min_profit:
                    cycle, p, est_out = best
                    try:
                        await bot.send_message(user_id, f"Opportunity (triangular) on {ctx.id} {cycle.name}: ~{p:.3f}% amount {trade_amount} {GLOBAL_START_SYMBOL}")
                    except Exception:
                        pass
                    if live_trade:
                        try:
                            final_q = await execute_tri_cycle_live(ctx, cycle, trade_amount, max_slip, GLOBAL_START_SYMBOL)
                        except Exception as e:
                            logging.error(f"Execution failed: {e}")
                            final_q = est_out
                    else:
                        final_q = est_out
                    await loop.run_in_executor(None, db_log_trade_sync, user_id, ctx.id, cycle.name, GLOBAL_START_SYMBOL, trade_amount, final_q, float(p), {"est": est_out, "live": live_trade})
                    try:
                        await bot.send_message(user_id, f"Done {ctx.id} {cycle.name} start={trade_amount} end={final_q:.6f} pnl={(final_q-trade_amount):.6f} {GLOBAL_START_SYMBOL}")
                    except Exception:
                        pass

            # Cross-exchange: for symbols present on >=2 ctxs
            # build unique symbol set across ctxs
            all_symbols=set()
            for ctx, _ in ctx_cycles:
                all_symbols.update([s for s in ctx.markets.keys() if "/" in s and s.endswith(f"/{GLOBAL_START_SYMBOL}")])
            # check each symbol
            for symbol in all_symbols:
                res = await check_cross_exchange_simple([c for c,_ in ctx_cycles], symbol, trade_amount)
                if res and res["profit_pct"] >= min_profit:
                    msg = f"Cross-exchange opp {symbol}: ~{res['profit_pct']:.3f}% buy@{res['buy_ctx'].id} sell@{res['sell_ctx'].id}"
                    logging.info(msg)
                    try: await bot.send_message(user_id, msg)
                    except: pass
                    if live_trade:
                        # Note: executing cross-exchange requires balances on both exchanges; here we only notify.
                        pass
                    await loop.run_in_executor(None, db_log_trade_sync, user_id, f"{res['buy_ctx'].id}->${res['sell_ctx'].id}", f"cross-{symbol}", GLOBAL_START_SYMBOL, trade_amount, res["est_out"], float(res["profit_pct"]), {"buy_price": res["buy_price"], "sell_price": res["sell_price"]})

            await asyncio.sleep(GLOBAL_SCAN_INTERVAL)
        except asyncio.CancelledError:
            logging.info(f"user_scan_loop {user_id} cancelled")
            break
        except Exception as e:
            logging.exception(f"Scan loop error user {user_id}: {e}")
            await asyncio.sleep(2)

# -------------------------
# Aiogram handlers (simple menu)
# -------------------------
main_kb = ReplyKeyboardMarkup(resize_keyboard=True)
main_kb.add(KeyboardButton("🔗 ربط منصة جديدة"))
main_kb.add(KeyboardButton("💰 تعيين مبلغ التداول"))
main_kb.add(KeyboardButton("▶️ تشغيل/ايقاف التداول"))
main_kb.add(KeyboardButton("📈 عرض الصفقات"))
main_kb.add(KeyboardButton("🧾 حساباتي"))

pending_add = {}
pending_amount = {}

@dp.message_handler(commands=["start"])
async def cmd_start(msg: types.Message):
    uid = await asyncio.get_event_loop().run_in_executor(None, db_add_user_sync, msg.from_user.id, msg.from_user.username)
    await msg.answer("تم التسجيل. استخدم القائمة.", reply_markup=main_kb)

@dp.message_handler(lambda m: m.text=="🔗 ربط منصة جديدة")
async def add_exchange_step1(msg: types.Message):
    pending_add[msg.from_user.id] = {"step":"ask_name"}
    await msg.answer("ادخل اسم المنصة (مثال: binance, kucoin, bitget):", reply_markup=ReplyKeyboardRemove())

@dp.message_handler(lambda m: m.from_user.id in pending_add and pending_add[m.from_user.id].get("step")=="ask_name")
async def add_exchange_step2(msg: types.Message):
    tg=msg.from_user.id; name=msg.text.strip().lower()
    pending_add[tg].update({"exchange_id": name, "step":"ask_key"})
    await msg.answer("ادخل API Key:")

@dp.message_handler(lambda m: m.from_user.id in pending_add and pending_add[m.from_user.id].get("step")=="ask_key")
async def add_exchange_step3(msg: types.Message):
    tg=msg.from_user.id
    pending_add[tg].update({"api_key": msg.text.strip(), "step":"ask_secret"})
    await msg.answer("ادخل API Secret:")

@dp.message_handler(lambda m: m.from_user.id in pending_add and pending_add[m.from_user.id].get("step")=="ask_secret")
async def add_exchange_step4(msg: types.Message):
    tg=msg.from_user.id
    pending_add[tg].update({"api_secret": msg.text.strip(), "step":"ask_pass"})
    await msg.answer("ادخل passphrase او '-' اذا غير مطلوب:")

@dp.message_handler(lambda m: m.from_user.id in pending_add and pending_add[m.from_user.id].get("step")=="ask_pass")
async def add_exchange_finish(msg: types.Message):
    tg=msg.from_user.id; data=pending_add.pop(tg)
    passphrase = "" if msg.text.strip() == "-" else msg.text.strip()
    user_row = await asyncio.get_event_loop().run_in_executor(None, db_get_user_by_tg_sync, tg)
    user_id = int(user_row[0])
    await asyncio.get_event_loop().run_in_executor(None, db_add_exchange_account_sync, user_id, data["exchange_id"], data["api_key"], data["api_secret"], passphrase, False)
    await msg.answer(f"تم إضافة حساب {data['exchange_id']}", reply_markup=main_kb)

@dp.message_handler(lambda m: m.text=="💰 تعيين مبلغ التداول")
async def set_amount_step(msg: types.Message):
    pending_amount[msg.from_user.id] = True
    await msg.answer("اكتب مبلغ التداول بالـ USDT (مثال: 10):", reply_markup=ReplyKeyboardRemove())

@dp.message_handler(lambda m: m.from_user.id in pending_amount)
async def set_amount_finish(msg: types.Message):
    try:
        val=float(msg.text.strip())
        user_row = await asyncio.get_event_loop().run_in_executor(None, db_get_user_by_tg_sync, msg.from_user.id)
        user_id = int(user_row[0])
        await asyncio.get_event_loop().run_in_executor(None, db_set_user_setting_sync, user_id, val, None, None, None, None)
        pending_amount.pop(msg.from_user.id, None)
        await msg.answer(f"تم حفظ مبلغ التداول = {val} USDT", reply_markup=main_kb)
    except Exception:
        await msg.answer("قيمة غير صحيحة. أكتب رقم مثل 10")

@dp.message_handler(lambda m: m.text=="▶️ تشغيل/ايقاف التداول")
async def toggle_running(msg: types.Message):
    tg = msg.from_user.id
    ur = await asyncio.get_event_loop().run_in_executor(None, db_get_user_by_tg_sync, tg)
    if not ur:
        await msg.answer("سجّل أولاً بـ /start", reply_markup=main_kb); return
    user_id=int(ur[0])
    s = await asyncio.get_event_loop().run_in_executor(None, db_get_user_setting_sync, user_id)
    running = bool(int(s[4])) if s else False
    if running:
        # stop
        t = user_tasks.get(user_id)
        if t:
            t.cancel(); user_tasks.pop(user_id, None)
        await asyncio.get_event_loop().run_in_executor(None, db_set_user_setting_sync, user_id, None, None, None, 0, None)
        await msg.answer("تم إيقاف التداول.", reply_markup=main_kb)
    else:
        # start
        if not s:
            await asyncio.get_event_loop().run_in_executor(None, db_set_user_setting_sync, user_id, 10.0, GLOBAL_MIN_PROFIT_PCT, GLOBAL_MAX_SLIPPAGE_PCT, 1, json.dumps([]))
        else:
            await asyncio.get_event_loop().run_in_executor(None, db_set_user_setting_sync, user_id, None, None, None, 1, None)
        # spawn background task
        user_tasks[user_id] = asyncio.create_task(user_scan_loop(user_id))
        await msg.answer("التداول شغال الآن (في الخلفية).", reply_markup=main_kb)

@dp.message_handler(lambda m: m.text=="📈 عرض الصفقات")
async def show_trades(msg: types.Message):
    ur = await asyncio.get_event_loop().run_in_executor(None, db_get_user_by_tg_sync, msg.from_user.id)
    if not ur: await msg.answer("سجّل أولًا بـ /start", reply_markup=main_kb); return
    uid=int(ur[0])
    with engine.begin() as conn:
        rows = conn.execute(text("SELECT exchange_id, cycle_name, start_amount, end_amount, profit_pct, created_at FROM trades WHERE user_id = :uid ORDER BY id DESC LIMIT 20"), {"uid": uid}).fetchall()
    if not rows:
        await msg.answer("لا توجد صفقات.", reply_markup=main_kb); return
    lines=["آخر الصفقات:"]
    for r in rows:
        lines.append(f"{r[5]} | {r[0]} | {r[1]} | start={r[2]} end={r[3]} pnl%={r[4]}")
    await msg.answer("\n".join(lines), reply_markup=main_kb)

@dp.message_handler(lambda m: m.text=="🧾 حساباتي")
async def my_accounts(msg: types.Message):
    ur = await asyncio.get_event_loop().run_in_executor(None, db_get_user_by_tg_sync, msg.from_user.id)
    if not ur: await msg.answer("سجّل أولًا بـ /start", reply_markup=main_kb); return
    uid=int(ur[0])
    accs = await asyncio.get_event_loop().run_in_executor(None, db_get_exchange_accounts_sync, uid)
    if not accs:
        await msg.answer("لا توجد حسابات مضافة.", reply_markup=main_kb); return
    lines=["حساباتك:"]
    for a in accs:
        lines.append(f"{a['exchange_id']} (testnet={a['testnet']})")
    await msg.answer("\n".join(lines), reply_markup=main_kb)

# -------------------------
# startup / shutdown
# -------------------------
async def on_startup(dp):
    # migrations sync
    await asyncio.get_event_loop().run_in_executor(None, migrate_sync)
    # spawn tasks for users that had live_trade=1
    with engine.begin() as conn:
        rows = conn.execute(text("SELECT user_id FROM user_settings WHERE live_trade = 1")).fetchall()
    for r in rows:
        uid=int(r[0])
        if uid not in user_tasks:
            user_tasks[uid] = asyncio.create_task(user_scan_loop(uid))
    logging.info("Startup complete.")

async def on_shutdown(dp):
    for t in list(user_tasks.values()):
        t.cancel()
    await bot.close()
    logging.info("Shutdown complete.")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup, on_shutdown=on_shutdown)
