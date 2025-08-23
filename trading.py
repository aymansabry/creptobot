# trading.py
import asyncio
import logging
from binance.client import AsyncClient
from binance.exceptions import BinanceAPIException
from db import save_last_trades, get_user_api_keys, get_amount
from decimal import Decimal, getcontext
from datetime import datetime

# Set precision for Decimal calculations to avoid floating-point errors
getcontext().prec = 28

logger = logging.getLogger(__name__)

ARBITRAGE_LOOP_ACTIVE = {}
MIN_PROFIT_PERCENT = Decimal('0.001') # Minimum profit threshold (e.g., 0.1%)

# Helper function to get the number of decimal places for a quantity
async def _get_quantity_precision(client, symbol):
    """
    Fetches the number of decimal places allowed for a symbol's quantity.
    """
    try:
        info = await client.get_symbol_info(symbol)
        if info:
            for f in info['filters']:
                if f['filterType'] == 'LOT_SIZE':
                    step_size = f['stepSize']
                    # Calculate precision from step_size
                    precision = int(abs(Decimal(step_size).log10()))
                    return precision
    except Exception as e:
        logger.error(f"Failed to get precision for {symbol}: {e}")
    return 8  # Default to 8 if not found

async def get_client_for_user(user_id):
    api_keys = get_user_api_keys(user_id)
    if not api_keys or 'api_key' not in api_keys or 'api_secret' not in api_keys:
        raise ValueError("API keys not registered for this user.")
    return AsyncClient(api_keys['api_key'], api_keys['api_secret'])

async def place_market_order(client, symbol, quantity, side):
    """
    Places a market order after rounding the quantity to the correct precision.
    """
    precision = await _get_quantity_precision(client, symbol)
    # Round the quantity to the correct number of decimal places
    rounded_quantity = round(Decimal(quantity), precision)
    
    if rounded_quantity <= 0:
        logger.error(f"Order quantity is zero or negative for {symbol} {side}")
        return None

    logger.info(f"Placing market order for {symbol} with quantity: {rounded_quantity}")
    try:
        order = await client.create_order(
            symbol=symbol,
            side=side,
            type='MARKET',
            quantity=f"{rounded_quantity}"
        )
        logger.info(f"Order placed successfully: {order}")
        return order
    except BinanceAPIException as e:
        logger.error(f"BinanceAPIException: {e}")
    except Exception as e:
        logger.error(f"place_market_order error {symbol} {side} {quantity}: {e}")
    return None

async def find_arbitrage_opportunity(client):
    """
    Finds a triangular arbitrage opportunity.
    This logic has been revised to be more robust.
    """
    logger.info("Fetching market data...")
    tickers = await client.get_ticker()
    
    ticker_dict = {t['symbol']: Decimal(t['price']) for t in tickers}
    
    # Example pairs for a common triangle (e.g., BTC, ETH, USDT)
    triangles = [
        ("BTCUSDT", "ETHBTC", "ETHUSDT"),
        ("ETHUSDT", "BTCETH", "BTCUSDT"),
    ]
    
    for triangle in triangles:
        symbol1, symbol2, symbol3 = triangle
        
        if not all(s in ticker_dict for s in triangle):
            continue

        try:
            # First leg
            rate1 = ticker_dict[symbol1]
            # Second leg
            rate2 = ticker_dict[symbol2]
            # Third leg
            rate3 = ticker_dict[symbol3]

            # Calculation for one direction (e.g., USDT -> BTC -> ETH -> USDT)
            profit_calculation_1 = (Decimal(1) / rate1) * rate2 * rate3
            profit_percent_1 = (profit_calculation_1 - 1) * 100

            if profit_percent_1 > MIN_PROFIT_PERCENT:
                return (triangle, profit_percent_1, "forward")
            
            # Calculation for reverse direction (e.g., USDT -> ETH -> BTC -> USDT)
            profit_calculation_2 = (Decimal(1) / rate3) * (Decimal(1) / rate2) * rate1
            profit_percent_2 = (profit_calculation_2 - 1) * 100

            if profit_percent_2 > MIN_PROFIT_PERCENT:
                return (triangle, profit_percent_2, "reverse")

        except Exception as e:
            logger.error(f"Error calculating triangle {triangle}: {e}")
            continue

    return None

async def start_arbitrage(user_id, context):
    if ARBITRAGE_LOOP_ACTIVE.get(user_id):
        await context.bot.send_message(chat_id=user_id, text="⚠️ التداول قيد التشغيل بالفعل.")
        return

    ARBITRAGE_LOOP_ACTIVE[user_id] = True
    amount = get_amount(user_id)

    try:
        client = await get_client_for_user(user_id)
    except ValueError as e:
        logger.error(e)
        await context.bot.send_message(chat_id=user_id, text=f"❌ خطأ: {e}")
        ARBITRAGE_LOOP_ACTIVE[user_id] = False
        return

    while ARBITRAGE_LOOP_ACTIVE.get(user_id):
        try:
            opportunity = await find_arbitrage_opportunity(client)
            
            if opportunity:
                triangle, profit_percent, direction = opportunity
                await context.bot.send_message(chat_id=user_id, text=f"🎉 تم العثور على فرصة! ربح محتمل: {profit_percent:.4f}% في مثلث {triangle}")
                
                # Execute the trade sequence
                if direction == "forward":
                    symbol1, symbol2, symbol3 = triangle
                    
                    # Step 1: Buy First Asset (e.g., BTC) with USDT
                    await context.bot.send_message(chat_id=user_id, text=f"1️⃣ شراء {symbol1}...")
                    order1 = await place_market_order(client, symbol1, amount, 'BUY')
                    if not order1: raise Exception("Failed order 1")
                    await asyncio.sleep(1) # Wait for order to fill
                    
                    # Step 2: Buy Second Asset (e.g., ETH) with the First Asset (BTC)
                    await context.bot.send_message(chat_id=user_id, text=f"2️⃣ شراء {symbol2}...")
                    # Calculate quantity for the next trade
                    quantity2 = Decimal(order1['executedQty']) / Decimal(order1['cummulativeQuoteQty']) * Decimal(order1['price'])
                    order2 = await place_market_order(client, symbol2, quantity2, 'BUY')
                    if not order2: raise Exception("Failed order 2")
                    await asyncio.sleep(1) # Wait for order to fill
                    
                    # Step 3: Sell the Second Asset (ETH) for USDT to complete the cycle
                    await context.bot.send_message(chat_id=user_id, text=f"3️⃣ بيع {symbol3}...")
                    quantity3 = Decimal(order2['executedQty'])
                    order3 = await place_market_order(client, symbol3, quantity3, 'SELL')
                    if not order3: raise Exception("Failed order 3")
                    await context.bot.send_message(chat_id=user_id, text="✅ تمت عملية التداول بالكامل.")
                    
                    # Calculate final profit
                    final_amount = Decimal(order3['cummulativeQuoteQty'])
                    profit = final_amount - Decimal(amount)
                    save_last_trades(user_id, f"{triangle[0]}-{triangle[1]}-{triangle[2]}", profit, datetime.utcnow())
                    await context.bot.send_message(chat_id=user_id, text=f"💰 نجاح! تم تسجيل ربح: {profit:.6f}$")

                # The same logic needs to be implemented for the "reverse" direction
                
            else:
                await context.bot.send_message(chat_id=user_id, text="🔍 لا توجد فرص تداول حالية. سأبحث مجدداً بعد دقيقة.")

        except Exception as e:
            logger.error(f"فشلت محاولة التداول: {e}")
            await context.bot.send_message(chat_id=user_id, text=f"❌ فشلت محاولة التداول: {e}")

        await asyncio.sleep(60) # Wait for 60 seconds before next attempt

async def stop_arbitrage(user_id):
    if ARBITRAGE_LOOP_ACTIVE.get(user_id):
        ARBITRAGE_LOOP_ACTIVE[user_id] = False
        logger.info(f"تم إيقاف حلقة التداول للمستخدم {user_id}.")