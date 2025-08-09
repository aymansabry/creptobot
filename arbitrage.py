# arbitrage.py
import os, logging
from database import query, execute
from notifications import send_notification_to_user, send_admin_alert
from binance_api import BinanceAPI
from kucoin_api import KucoinAPI
import openai
from decimal import Decimal, ROUND_DOWN

openai.api_key = os.getenv("OPENAI_API_KEY")
MIN_PROFIT = Decimal(os.getenv("MIN_PROFIT_PERCENTAGE", "3"))
STOP_LOSS = Decimal(os.getenv("STOP_LOSS_PERCENTAGE", "2"))

def ai_confirm_opportunity(prices):
    # simple deterministic prompt + check
    try:
        prompt = f"أسعار: {prices}. هل فرصة مراجحة بأكثر من {MIN_PROFIT}%؟ أجب نعم أو لا."
        resp = openai.Completion.create(engine="text-davinci-003", prompt=prompt, max_tokens=6, temperature=0)
        ans = resp.choices[0].text.strip().lower()
        return "نعم" in ans or "yes" in ans
    except Exception as e:
        logging.error("OpenAI error: %s", e)
        return False

def compute_profit_pct(buy_price, sell_price):
    return (Decimal(sell_price) - Decimal(buy_price)) / Decimal(buy_price) * Decimal(100)

def execute_arbitrage_for_user(user):
    # user is dict from DB
    if not user['is_active']:
        return
    if user['demo_mode']:
        # demo mode: simulate only
        simulate_and_record(user)
        return

    # ensure keys present
    if not user['api_binance_key'] or not user['api_kucoin_key']:
        send_notification_to_user(user['id'], "API keys ناقصة — الرجاء ضبط مفاتيح Binance/Kucoin.")
        return

    try:
        b = BinanceAPI(user['api_binance_key'], user['api_binance_secret'])
        k = KucoinAPI(user['api_kucoin_key'], user['api_kucoin_secret'], user.get('api_kucoin_pass') or os.getenv('KUCOIN_API_PASSPHRASE'))

        # choose symbol e.g. USDT/USDT is nonsense — adapt to real trading pairs; for demo use BTCUSDT
        symbol_b = os.getenv("BINANCE_SYMBOL", "BTCUSDT")
        symbol_k = os.getenv("KUCOIN_SYMBOL", "BTC-USDT")

        price_b = b.get_symbol_price(symbol_b)
        price_k = k.get_symbol_price(symbol_k)

        prices = {'Binance': price_b, 'Kucoin': price_k}
        if not ai_confirm_opportunity(prices):
            return

        profit_pct = compute_profit_pct(price_b, price_k)
        if profit_pct < MIN_PROFIT:
            send_notification_to_user(user['id'], f"الفرصة أقل من الحد ({profit_pct:.2f}%).")
            return

        # verify balances
        invested = Decimal(user['invested_amount'])
        bal_b = Decimal(b.get_account_balance('USDT'))
        bal_k = Decimal(k.get_account_balance('USDT'))
        if invested > bal_b:
            send_notification_to_user(user['id'], "الرصيد في Binance لا يكفي.")
            return
        # execute market buy on Binance, market sell on Kucoin
        qty = (invested / Decimal(price_b)).quantize(Decimal('0.00000001'), rounding=ROUND_DOWN)
        res_buy = b.create_order_market(symbol_b, 'BUY', float(qty))
        res_sell = k.create_order_market(symbol_k, 'SELL', str(float(qty)))

        # record trades
        platform_b = query("SELECT id FROM platforms WHERE name='Binance'", fetchone=True)['id']
        platform_k = query("SELECT id FROM platforms WHERE name='Kucoin'", fetchone=True)['id']
        execute("""
            INSERT INTO trades (user_id, platform_id, trade_type, asset, amount, price, profit, commission, status)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'completed')
        """, (user['id'], platform_b, 'buy', symbol_b, float(qty), float(price_b), float(profit_pct), float(user['commission_rate'])))
        execute("""
            INSERT INTO trades (user_id, platform_id, trade_type, asset, amount, price, profit, commission, status)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'completed')
        """, (user['id'], platform_k, 'sell', symbol_k, float(qty), float(price_k), float(profit_pct), float(user['commission_rate'])))

        send_notification_to_user(user['id'], f"تم تنفيذ مراجحة بحجم {invested} (ربح تقريبي {profit_pct:.2f}%).")
    except Exception as e:
        logging.exception("Arbitrage execution error for user %s: %s", user.get('id'), e)
        send_admin_alert("خطأ تنفيذ المراجحة", f"المستخدم {user.get('id')} - خطأ: {e}")

def simulate_and_record(user):
    # simulation record only
    price_b = 100
    price_k = 104
    profit_pct = compute_profit_pct(price_b, price_k)
    platform_b = query("SELECT id FROM platforms WHERE name='Binance'", fetchone=True)['id']
    platform_k = query("SELECT id FROM platforms WHERE name='Kucoin'", fetchone=True)['id']
    execute("""INSERT INTO trades (user_id, platform_id, trade_type, asset, amount, price, profit, commission, status)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'completed')""",
            (user['id'], platform_b, 'buy', 'SIM', float(user['invested_amount']), price_b, float(profit_pct), 0.0))
    execute("""INSERT INTO trades (user_id, platform_id, trade_type, asset, amount, price, profit, commission, status)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'completed')""",
            (user['id'], platform_k, 'sell', 'SIM', float(user['invested_amount']), price_k, float(profit_pct), 0.0))
