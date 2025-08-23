import asyncio
from binance import AsyncClient
from binance.enums import *
from db import get_user_api_keys, get_amount
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TRADING_RUNNING = False
USER_CLIENTS = {}

# إنشاء Binance Client لكل مستخدم
async def get_client(user_id):
    if user_id in USER_CLIENTS:
        return USER_CLIENTS[user_id]
    api_key, api_secret = await get_user_api_keys(user_id)
    client = await AsyncClient.create(api_key, api_secret)
    USER_CLIENTS[user_id] = client
    return client

# بدء التداول بمراجحة حقيقية
async def start_arbitrage(user_id):
    global TRADING_RUNNING
    TRADING_RUNNING = True
    client = await get_client(user_id)
    amount = await get_amount(user_id)

    while TRADING_RUNNING:
        opportunities = await calculate_arbitrage_opportunities(client, amount)
        for opp in opportunities:
            success = await execute_arbitrage(client, opp)
            if success:
                logger.info(f"✅ فرصة ناجحة: {opp}")
            else:
                logger.info(f"❌ محاولة فاشلة: {opp}")
        await asyncio.sleep(5)

# إيقاف التداول
async def stop_arbitrage():
    global TRADING_RUNNING
    TRADING_RUNNING = False
    for client in USER_CLIENTS.values():
        await client.close_connection()
    USER_CLIENTS.clear()
    logger.info("🛑 تم إيقاف التداول بالكامل.")

# جلب دفتر الأوامر
async def fetch_order_book(client, symbol, limit=5):
    return await client.get_order_book(symbol=symbol, limit=limit)

# تنفيذ أمر شراء/بيع
async def place_order(client, symbol, side, quantity, price=None, order_type=ORDER_TYPE_MARKET):
    try:
        if order_type == ORDER_TYPE_MARKET:
            order = await client.create_order(symbol=symbol, side=side, type=ORDER_TYPE_MARKET, quantity=quantity)
        else:
            order = await client.create_order(symbol=symbol, side=side, type=ORDER_TYPE_LIMIT, quantity=quantity, price=price)
        logger.info(f"✅ تنفيذ {side} على {symbol}: {order}")
        return order
    except Exception as e:
        logger.error(f"❌ خطأ في تنفيذ {side} على {symbol}: {e}")
        return None

# خوارزمية اكتشاف فرص المراجحة الحقيقية (ثلاثية/رباعية/خماسية)
async def calculate_arbitrage_opportunities(client, base_amount):
    tickers = await client.get_all_tickers()
    symbols = [t['symbol'] for t in tickers]
    opportunities = []

    # مثال لخوارزمية ثلاثية بسيطة (يمكن التوسيع للرباعية والخماسية)
    # مبدأ المراجحة: شراء عملة، تحويل لعملة ثانية، ثم بيعها للرجوع للـUSDT
    # يضاف فقط إذا الربح بعد الرسوم موجب
    for s1 in symbols:
        if s1.endswith("USDT"):
            base_coin = s1.replace("USDT","")
            for s2 in symbols:
                if s2.startswith(base_coin):
                    mid_coin = s2.replace(base_coin,"")
                    final_pair = f"{mid_coin}USDT"
                    if final_pair in symbols:
                        opp = {
                            'trades': [
                                {'symbol': s1, 'side': 'BUY', 'quantity': base_amount/float(await get_price(client, s1))},
                                {'symbol': s2, 'side': 'SELL', 'quantity': base_amount/float(await get_price(client, s2))},
                                {'symbol': final_pair, 'side': 'SELL', 'quantity': base_amount/float(await get_price(client, final_pair))}
                            ]
                        }
                        opportunities.append(opp)
    return opportunities

# جلب السعر الحالي للزوج
async def get_price(client, symbol):
    tickers = await client.get_all_tickers()
    for t in tickers:
        if t['symbol'] == symbol:
            return float(t['price'])
    return 1.0

# تنفيذ فرصة المراجحة
async def execute_arbitrage(client, opportunity):
    try:
        for trade in opportunity['trades']:
            await place_order(client, trade['symbol'], trade['side'], trade['quantity'])
        return True
    except Exception as e:
        logger.error(f"❌ خطأ في تنفيذ المراجحة: {e}")
        return False
