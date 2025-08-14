import asyncio
import ccxt
from db.encryption import decrypt_value
import logging

logger = logging.getLogger(__name__)

async def execute_order_on_exchange(exchange_id, order_type, symbol, amount, price, creds):
    exchange_class = getattr(ccxt, exchange_id.lower(), None)
    if not exchange_class:
        return False
    exchange = exchange_class({
        'apiKey': decrypt_value(creds.api_key),
        'secret': decrypt_value(creds.secret),
        'password': decrypt_value(creds.passphrase or '')
    })
    try:
        if order_type.lower() == 'buy':
            await asyncio.to_thread(exchange.create_limit_buy_order, symbol, amount, price)
        else:
            await asyncio.to_thread(exchange.create_limit_sell_order, symbol, amount, price)
        return True
    except Exception as e:
        logger.error(f"Order execution failed: {e}")
        return False