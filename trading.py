# trading.py
import asyncio
import logging
from binance.client import AsyncClient
from binance.exceptions import BinanceAPIException
# Corrected import name: save_last_trades instead of save_last_trade
from db import save_last_trades, get_user_api_keys
from decimal import Decimal, getcontext

# Set precision for Decimal calculations
getcontext().prec = 28

logger = logging.getLogger(__name__)

ARBITRAGE_LOOP_ACTIVE = {}

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
                    precision = int(round(-Decimal(step_size).log10(), 0))
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

async def start_arbitrage(user_id):
    if ARBITRAGE_LOOP_ACTIVE.get(user_id):
        return

    ARBITRAGE_LOOP_ACTIVE[user_id] = True
    try:
        client = await get_client_for_user(user_id)
    except ValueError as e:
        logger.error(e)
        return

    while ARBITRAGE_LOOP_ACTIVE.get(user_id):
        try:
            # Placeholder for arbitrage logic.
            # This is where your code would find arbitrage opportunities and place orders.
            # Example: finding a simple arbitrage opportunity and placing a trade
            # This part needs to be implemented to use place_market_order correctly.
            
            # For demonstration purposes, let's assume a dummy trade.
            # You will replace this with your actual trading logic.
            
            # Placeholder: Assume we found an opportunity for a WUSDT trade
            symbol = "WUSDT"
            # Note: The quantity here will be a result of a complex calculation
            quantity_to_trade = Decimal('59.400000000000006')
            
            # Place buy order
            buy_order = await place_market_order(client, symbol, quantity_to_trade, 'BUY')
            if not buy_order:
                raise Exception("Failed to place buy order")
            
            # Place sell order (for the sake of example)
            sell_order = await place_market_order(client, symbol, quantity_to_trade, 'SELL')
            if not sell_order:
                raise Exception("Failed to place sell order")

            # Simulate profit for the example
            profit_usd = Decimal('0.00123')
            # Corrected function call: save_last_trades
            save_last_trades(user_id, symbol, profit_usd, datetime.utcnow())
            
        except Exception as e:
            logger.error(f"Arbitrage attempt failed: {e}")

        await asyncio.sleep(60) # Wait for 60 seconds before next attempt

async def stop_arbitrage(user_id):
    if ARBITRAGE_LOOP_ACTIVE.get(user_id):
        ARBITRAGE_LOOP_ACTIVE[user_id] = False
        logger.info(f"Arbitrage loop for user {user_id} stopped.")