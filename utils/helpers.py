import asyncio
import ccxt
import logging
from db.encryption import decrypt_value

logger = logging.getLogger(__name__)

async def execute_order_on_exchange(exchange_id, order_type, symbol, amount, price, creds):
    exchange_class = getattr(ccxt, exchange_id.lower(), None)
    if not exchange_class:
        logger.error(f"Exchange class not found: {exchange_id}")
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
        logger.error(f"Order execution error on {exchange_id} for {symbol}: {e}")
        return False

async def analyze_with_openai(symbol, buy_price, sell_price):
    import openai, os
    openai.api_key = os.environ.get("OPENAI_API_KEY")
    prompt = (
        f"تحليل سريع لزوج {symbol}:\n"
        f"سعر الشراء: {buy_price}\n"
        f"سعر البيع: {sell_price}\n"
        f"اعطِ توقع إذا سيزيد السعر أم سينخفض خلال دقائق قادمة."
    )
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=60
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        logger.error(f"OpenAI analysis error: {e}")
        return "لا يمكن الحصول على تحليل حالياً."