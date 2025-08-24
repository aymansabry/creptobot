# main.py
# This is a single, self-contained file for the trading bot, compatible with Replit.
# It includes the bot logic, trading logic, and a simple in-memory database.

import os
import asyncio
import logging
from typing import List, Dict, Any, Tuple, Optional
import math
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from flask import Flask
from threading import Thread
from binance import AsyncClient
from binance.enums import ORDER_TYPE_MARKET, SIDE_BUY, SIDE_SELL

# ----------------- إعدادات التسجيل (Logging) -----------------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("TradingBot")

# ----------------- قاعدة بيانات بسيطة (في الذاكرة) -----------------
# Mock database (in-memory dictionary)
# In a real app, this data would be stored in Supabase/Firestore
USER_DATA = {}  # {telegram_id: {'api_key': '...', 'api_secret': '...', 'amount': '...'}}
TRADING_RUNNING = {}  # A flag for each user to indicate if the trading loop is active
USER_CLIENTS = {}  # A cache for Binance clients for each user
EXCHANGE_INFO_CACHE = {}  # A cache for exchange information

def save_user_api_keys(telegram_id: int, api_key: str, api_secret: str):
    """Saves user API keys to the database."""
    if telegram_id not in USER_DATA:
        USER_DATA[telegram_id] = {}
    USER_DATA[telegram_id]['api_key'] = api_key
    USER_DATA[telegram_id]['api_secret'] = api_secret
    logger.info(f"API keys saved for user {telegram_id}.")

def get_user_api_keys(telegram_id: int) -> Tuple[Optional[str], Optional[str]]:
    """Retrieves user API keys from the database."""
    data = USER_DATA.get(telegram_id, {})
    return data.get('api_key'), data.get('api_secret')

def save_amount(telegram_id: int, amount: float):
    """Saves the trading amount for a user."""
    if telegram_id not in USER_DATA:
        USER_DATA[telegram_id] = {}
    USER_DATA[telegram_id]['amount'] = amount
    logger.info(f"Amount {amount} saved for user {telegram_id}.")

def get_amount(telegram_id: int) -> float:
    """Retrieves the trading amount for a user."""
    data = USER_DATA.get(telegram_id, {})
    return data.get('amount', 10.0)  # Default to 10 USDT if not set

def add_trade(telegram_id: int, path: str, profit: float):
    """Logs a successful trade."""
    logger.info(f"User {telegram_id} completed a trade. Path: {path}, Profit: {profit}")
    # In a real app, you would save this to a 'trades' table in your database.

# ----------------- وظائف التداول (Trading Logic) -----------------

async def get_client_for_user(telegram_id: int) -> AsyncClient:
    """Creates or returns a cached AsyncClient for a user."""
    if telegram_id in USER_CLIENTS:
        return USER_CLIENTS[telegram_id]

    api_key, api_secret = get_user_api_keys(telegram_id)
    if not api_key or not api_secret:
        raise ValueError("API keys not found for user.")
    
    client = await AsyncClient.create(api_key, api_secret)
    USER_CLIENTS[telegram_id] = client
    return client

async def close_clients():
    """Closes all cached client connections."""
    for c in list(USER_CLIENTS.values()):
        try:
            await c.close_connection()
        except Exception:
            pass
    USER_CLIENTS.clear()

async def get_exchange_info(client: AsyncClient, symbol: str) -> Dict[str, Any]:
    """Fetches exchange information for a given symbol with caching."""
    if symbol in EXCHANGE_INFO_CACHE:
        return EXCHANGE_INFO_CACHE[symbol]
    info = await client.get_symbol_info(symbol=symbol)
    if info:
        EXCHANGE_INFO_CACHE[symbol] = info
    return info

def get_symbol_step_size(info: Dict[str, Any]) -> float:
    """Extracts the stepSize from symbol info."""
    for f in info['filters']:
        if f['filterType'] == 'LOT_SIZE':
            return float(f['stepSize'])
    return 0.0

def get_symbol_min_notional(info: Dict[str, Any]) -> float:
    """Extracts the minNotional from symbol info."""
    for f in info['filters']:
        if f['filterType'] == 'MIN_NOTIONAL':
            return float(f['minNotional'])
    return 0.0

def floor_quantity_to_step_size(quantity: float, step_size: float) -> float:
    """Rounds down the quantity to fit the step size."""
    if step_size == 0:
        return 0.0
    return math.floor(quantity / step_size) * step_size

async def check_user_balance(client: AsyncClient, trading_amount: float) -> bool:
    """Checks if the user has sufficient USDT balance."""
    try:
        info = await client.get_account()
        usdt_balance = 0.0
        for asset in info['balances']:
            if asset['asset'] == 'USDT':
                usdt_balance = float(asset['free'])
                break
        return usdt_balance >= trading_amount
    except Exception as e:
        logger.error(f"Error checking balance: {e}")
        return False

async def start_arbitrage(telegram_id: int):
    """Starts the long-running arbitrage loop for a specific user."""
    TRADING_RUNNING[telegram_id] = True
    try:
        client = await get_client_for_user(telegram_id)
        trading_amount_usdt = get_amount(telegram_id)
        
        if not await check_user_balance(client, trading_amount_usdt):
            logger.error(f"Cannot start arbitrage for {telegram_id}: Insufficient balance.")
            TRADING_RUNNING.pop(telegram_id, None)
            return
            
    except Exception as e:
        logger.error(f"Cannot start arbitrage for {telegram_id}: {e}")
        TRADING_RUNNING.pop(telegram_id, None)
        return

    logger.info(f"Starting arbitrage loop for {telegram_id} with {trading_amount_usdt} USDT.")

    while TRADING_RUNNING.get(telegram_id):
        try:
            opportunities = await calculate_arbitrage_opportunities(client)
            for opp in opportunities:
                ok = await execute_arbitrage(client, telegram_id, opp, trading_amount_usdt)
                if ok:
                    logger.info("Executed arbitrage successfully")
                else:
                    logger.info("Arbitrage attempt failed")
                break 
            
            await asyncio.sleep(3)
        except Exception as e:
            logger.exception("Error in arbitrage loop: %s", e)
            await asyncio.sleep(2)

    logger.info(f"Arbitrage loop stopped for {telegram_id}")

async def stop_arbitrage(telegram_id: int = None):
    """Stops trading for a specific user or all users if telegram_id is None."""
    if telegram_id is None:
        for k in list(TRADING_RUNNING.keys()):
            TRADING_RUNNING[k] = False
        await close_clients()
        logger.info("Stopped all arbitrage loops")
    else:
        TRADING_RUNNING[telegram_id] = False
        client = USER_CLIENTS.pop(telegram_id, None)
        if client:
            try:
                await client.close_connection()
            except Exception:
                pass
        logger.info(f"Stopped arbitrage for {telegram_id}")

async def place_market_order(client: AsyncClient, symbol: str, side: str, quantity: float):
    """Places a market order, ensuring the quantity fits exchange rules."""
    try:
        order = await client.create_order(
            symbol=symbol,
            side=side,
            type=ORDER_TYPE_MARKET,
            quantity=quantity
        )
        logger.info(f"Order placed: {order}")
        return order
    except Exception as e:
        logger.error(f"place_market_order error {symbol} {side} {quantity}: {e}")
        return None

async def get_price(client: AsyncClient, symbol: str) -> float:
    """Fetches the current price of a symbol."""
    try:
        ticker = await client.get_symbol_ticker(symbol=symbol)
        return float(ticker["price"])
    except Exception:
        return 0.0

async def calculate_arbitrage_opportunities(client: AsyncClient) -> List[Dict[str, Any]]:
    """
    Detects triangular, quadrilateral, and pentagonal arbitrage opportunities.
    Returns a list of opportunities sorted by estimated profit.
    """
    tickers = await client.get_all_tickers()
    symbols = [t["symbol"] for t in tickers]
    price_map = {t["symbol"]: float(t["price"]) for t in tickers}

    opportunities = []
    TRADING_FEE = 0.001

    def has(sym):
        return sym in price_map

    # --- Triangular Arbitrage: A/USDT -> A/B -> B/USDT ---
    for s_a_usdt in [s for s in symbols if s.endswith("USDT")]:
        coin_a = s_a_usdt[:-4]
        for s_a_b in [s for s in symbols if s.startswith(coin_a) and s != s_a_usdt]:
            coin_b = s_a_b[len(coin_a):]
            final = f"{coin_b}USDT"
            if not has(final):
                continue
            
            pa = price_map[s_a_usdt]
            pab = price_map[s_a_b]
            pfinal = price_map[final]
            try:
                final_usdt = (1.0 * (1 - TRADING_FEE) / pa) * pab * (1 - TRADING_FEE) * pfinal * (1 - TRADING_FEE)
                est_profit = final_usdt - 1.0
                if est_profit > 0.0001:
                    opp = {
                        "type": "tri",
                        "path": [s_a_usdt, s_a_b, final],
                        "est_profit_ratio": est_profit,
                    }
                    opportunities.append(opp)
            except Exception:
                continue

    # --- Quadrilateral Arbitrage: A/USDT -> A/B -> B/C -> C/USDT ---
    for s_a_usdt in [s for s in symbols if s.endswith("USDT")]:
        coin_a = s_a_usdt[:-4]
        for s_a_b in [s for s in symbols if s.startswith(coin_a) and s != s_a_usdt]:
            coin_b = s_a_b[len(coin_a):]
            for s_b_c in [s for s in symbols if s.startswith(coin_b) and s not in (s_a_b, s_a_usdt)]:
                coin_c = s_b_c[len(coin_b):]
                final = f"{coin_c}USDT"
                if not has(final):
                    continue
                try:
                    pa = price_map[s_a_usdt]
                    pab = price_map[s_a_b]
                    pbc = price_map[s_b_c]
                    pfinal = price_map[final]
                    final_usdt = (1.0 * (1 - TRADING_FEE) / pa) * pab * (1 - TRADING_FEE) * pbc * (1 - TRADING_FEE) * pfinal * (1 - TRADING_FEE)
                    est_profit = final_usdt - 1.0
                    if est_profit > 0.00015:
                        opp = {
                            "type": "quad",
                            "path": [s_a_usdt, s_a_b, s_b_c, final],
                            "est_profit_ratio": est_profit,
                        }
                        opportunities.append(opp)
                except Exception:
                    continue
                    
    # --- Pentagonal Arbitrage (5 steps) ---
    for s_a_usdt in [s for s in symbols if s.endswith("USDT")]:
        coin_a = s_a_usdt[:-4]
        for s_a_b in [s for s in symbols if s.startswith(coin_a) and s != s_a_usdt]:
            coin_b = s_a_b[len(coin_a):]
            for s_b_c in [s for s in symbols if s.startswith(coin_b) and s not in (s_b_c, s_a_b)]:
                coin_c = s_b_c[len(coin_b):]
                for s_c_d in [s for s in symbols if s.startswith(coin_c) and s not in (s_b_c, s_a_b, s_a_usdt)]:
                    coin_d = s_c_d[len(coin_c):]
                    final = f"{coin_d}USDT"
                    if not has(final):
                        continue
                    try:
                        pa = price_map[s_a_usdt]
                        pab = price_map[s_a_b]
                        pbc = price_map[s_b_c]
                        pcd = price_map[s_c_d]
                        pfinal = price_map[final]
                        final_usdt = (1.0 * (1 - TRADING_FEE) / pa) * pab * (1 - TRADING_FEE) * pbc * (1 - TRADING_FEE) * pcd * (1 - TRADING_FEE) * pfinal * (1 - TRADING_FEE)
                        est_profit = final_usdt - 1.0
                        if est_profit > 0.0002:
                            opp = {
                                "type": "penta",
                                "path": [s_a_usdt, s_a_b, s_b_c, s_c_d, final],
                                "est_profit_ratio": est_profit,
                            }
                            opportunities.append(opp)
                    except Exception:
                        continue


    opportunities.sort(key=lambda x: x["est_profit_ratio"], reverse=True)
    return opportunities[:10]

async def sell_to_usdt(client: AsyncClient, asset: str) -> bool:
    """Rollback function: sells the specified asset to USDT."""
    symbol = f"{asset}USDT"
    try:
        balances = await client.get_account()
        qty = 0.0
        for bal in balances['balances']:
            if bal['asset'] == asset:
                qty = float(bal['free'])
                break
        if qty > 0:
            info = await get_exchange_info(client, symbol)
            if not info: return False
            step_size = get_symbol_step_size(info)
            min_notional = get_symbol_min_notional(info)
            corrected_qty = floor_quantity_to_step_size(qty, step_size)
            price = await get_price(client, symbol)
            if corrected_qty * price < min_notional:
                logger.warning(f"Rollback: Corrected quantity {corrected_qty} for {symbol} is too low to sell.")
                return False
            res = await place_market_order(client, symbol, SIDE_SELL, corrected_qty)
            return bool(res)
        return False
    except Exception as e:
        logger.error(f"Rollback failed for {asset}: {e}")
        return False

async def execute_arbitrage(client: AsyncClient, telegram_id: int, opportunity: dict, usd_amount: float):
    """
    Converts the opportunity path into actual market orders.
    """
    path = opportunity.get("path", [])
    current_asset_quantity = usd_amount
    
    try:
        for i, symbol in enumerate(path):
            info = await get_exchange_info(client, symbol)
            if not info:
                logger.error(f"Could not get exchange info for {symbol}")
                return False
            min_notional = get_symbol_min_notional(info)

            if symbol.endswith("USDT"):
                price = await get_price(client, symbol)
                if price <= 0: return False
                raw_qty = current_asset_quantity / price
                step_size = get_symbol_step_size(info)
                qty = floor_quantity_to_step_size(raw_qty, step_size)
                if qty * price < min_notional:
                    logger.warning(f"Order quantity {qty} for {symbol} is below min notional {min_notional}.")
                    return False
                res = await place_market_order(client, symbol, SIDE_BUY, qty)
                if not res: return False
                current_asset_quantity = float(res['executedQty'])
            else:
                base_asset = info['baseAsset']
                quote_asset = info['quoteAsset']
                if path[i-1].endswith(base_asset):
                    side = SIDE_SELL
                    price = await get_price(client, symbol)
                    if price <= 0: return False
                    raw_qty = current_asset_quantity
                    step_size = get_symbol_step_size(info)
                    qty = floor_quantity_to_step_size(raw_qty, step_size)
                    if qty * price < min_notional:
                        logger.warning(f"Order quantity {qty} for {symbol} is below min notional {min_notional}.")
                        return False
                    res = await place_market_order(client, symbol, side, qty)
                    if not res:
                        await sell_to_usdt(client, base_asset)
                        return False
                    current_asset_quantity = float(res['executedQty'])
                else:
                    side = SIDE_BUY
                    price = await get_price(client, symbol)
                    if price <= 0: return False
                    raw_qty = current_asset_quantity / price
                    step_size = get_symbol_step_size(info)
                    qty = floor_quantity_to_step_size(raw_qty, step_size)
                    if qty * price < min_notional:
                        logger.warning(f"Order quantity {qty} for {symbol} is below min notional {min_notional}.")
                        return False
                    res = await place_market_order(client, symbol, side, qty)
                    if not res:
                        await sell_to_usdt(client, quote_asset)
                        return False
                    current_asset_quantity = float(res['executedQty'])

        final_usdt_quantity = current_asset_quantity
        profit = final_usdt_quantity - usd_amount
        add_trade(telegram_id, ",".join(path), profit)
        logger.info(f"Arbitrage success! Final profit: {profit} USDT.")
        return True
    
    except Exception as e:
        logger.exception("execute_arbitrage error: %s", e)
        path_assets = [p.replace('USDT', '') for p in path]
        current_asset = path_assets[i]
        await sell_to_usdt(client, current_asset)
        return False

# ----------------- أوامر البوت (Bot Commands) -----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logger.info(f"User {user_id} started the bot.")
    await update.message.reply_text(
        'مرحباً! أنا بوت تداول. استخدم الأوامر التالية:\n'
        '\n'
        '/set_api_keys <api_key> <api_secret>\n'
        '/set_amount <amount>\n'
        '/start_trading\n'
        '/stop_trading'
    )

async def set_api_keys(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        api_key, api_secret = context.args
        user_id = update.effective_user.id
        save_user_api_keys(user_id, api_key, api_secret)
        logger.info(f"API keys saved for user {user_id}.")
        await update.message.reply_text("تم حفظ مفاتيح API بنجاح.")
    except (IndexError, ValueError):
        await update.message.reply_text("الرجاء إدخال المفاتيح بالشكل الصحيح: /set_api_keys <api_key> <api_secret>")

async def set_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(context.args[0])
        user_id = update.effective_user.id
        save_amount(user_id, amount)
        logger.info(f"Trading amount {amount} saved for user {user_id}.")
        await update.message.reply_text(f"تم تعيين مبلغ التداول على {amount} دولار بنجاح.")
    except (IndexError, ValueError):
        await update.message.reply_text("الرجاء إدخال المبلغ بالشكل الصحيح: /set_amount <amount>")

async def start_trading_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logger.info(f"Received start_trading command from {user_id}.")
    await update.message.reply_text("بدء التداول...")
    asyncio.create_task(start_arbitrage(user_id))

async def stop_trading_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logger.info(f"Received stop_trading command from {user_id}.")
    await update.message.reply_text("إيقاف التداول...")
    await stop_arbitrage(user_id)

# ----------------- وظائف Flask (لإبقاء البوت نشطًا) -----------------
app = Flask(__name__)
@app.route('/')
def home():
    return "The bot is alive!"

def run_flask_app():
    port = os.environ.get("PORT", 8080)
    app.run(host='0.0.0.0', port=port)

# ----------------- التشغيل الرئيسي -----------------
async def main():
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set.")
        return

    application = Application.builder().token(bot_token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("set_api_keys", set_api_keys))
    application.add_handler(CommandHandler("set_amount", set_amount))
    application.add_handler(CommandHandler("start_trading", start_trading_command))
    application.add_handler(CommandHandler("stop_trading", stop_trading_command))

    await application.run_polling(poll_interval=1)

if __name__ == "__main__":
    flask_thread = Thread(target=run_flask_app)
    flask_thread.start()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")