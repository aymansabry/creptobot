
# arbitrage.py
import os
import logging
from decimal import Decimal, ROUND_DOWN
from database import query, query_one, execute
from utils import send_notification_to_user, send_admin_alert
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")
MIN_PROFIT = Decimal(os.getenv("ARBITRAGE_MIN_PROFIT", "3"))
# Note: real exchange API code inserted here in production.

logger = logging.getLogger(__name__)

def ai_confirm_opportunity(buy_price, sell_price):
    """
    Use OpenAI or simple calculation to confirm opportunity.
    Keep prompt minimal and deterministic (safety).
    """
    try:
        profit_pct = ((Decimal(sell_price) - Decimal(buy_price)) / Decimal(buy_price)) * Decimal(100)
        return profit_pct >= MIN_PROFIT, profit_pct
    except Exception as e:
        logger.exception("ai_confirm_opportunity error: %s", e)
        return False, Decimal(0)

def execute_arbitrage_for_user(user):
    """
    user: dict row from users table
    This function attempts to execute arbitrage for a single user.
    It should:
      - verify keys exist
      - check balances (use exchange SDKs)
      - compute quantity
      - execute market orders (buy then sell)
      - record trades and notify
    For safety, this code includes placeholders where to plug exchange clients.
    """
    if not user.get("is_active"):
        return

    try:
        # demo mode: simulate
        if user.get("demo_mode"):
            buy_price = Decimal("100")
            sell_price = Decimal("104")
            ok, profit_pct = ai_confirm_opportunity(buy_price, sell_price)
            if ok:
                # record simulated trades
                platform_b = query_one("SELECT id FROM platforms WHERE name='Binance'")['id']
                platform_k = query_one("SELECT id FROM platforms WHERE name='Kucoin'")['id']
                amt = Decimal(user.get("invested_amount") or "0")
                if amt <= 0:
                    send_notification_to_user(user['id'], "رصيد الاستثمار صفر. حدده عبر الإعدادات.")
                    return
                qty = (amt / buy_price).quantize(Decimal('0.00000001'), rounding=ROUND_DOWN)
                execute("INSERT INTO trades (user_id, platform_id, trade_type, asset, amount, price, profit, commission, status) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'completed')",
                        (user['id'], platform_b, 'buy', 'SIM', float(qty), float(buy_price), float(profit_pct), float(user.get('commission_rate') or 0.0)))
                execute("INSERT INTO trades (user_id, platform_id, trade_type, asset, amount, price, profit, commission, status) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'completed')",
                        (user['id'], platform_k, 'sell', 'SIM', float(qty), float(sell_price), float(profit_pct), float(user.get('commission_rate') or 0.0)))
                send_notification_to_user(user['id'], f"[Demo] تم محاكاة مراجحة — ربح متوقع {profit_pct:.2f}%")
            return

        # Real mode (placeholders)
        # Verify API keys present
        if not (user.get("api_binance_key") and user.get("api_binance_secret") and user.get("api_kucoin_key") and user.get("api_kucoin_secret")):
            send_notification_to_user(user['id'], "مفاتيح API ناقصة — الرجاء ضبطها في الإعدادات.")
            return

        # TODO: instantiate exchange clients (BinanceAPI, KucoinAPI), fetch prices and balances
        # Example pseudocode:
        # b = BinanceAPI(user['api_binance_key'], user['api_binance_secret'])
        # k = KucoinAPI(user['api_kucoin_key'], user['api_kucoin_secret'], user.get('api_kucoin_pass'))
        # buy_price = b.get_symbol_price('BTCUSDT')
        # sell_price = k.get_symbol_price('BTC-USDT')
        # ok, profit_pct = ai_confirm_opportunity(buy_price, sell_price)
        # if ok: execute market buy and sell, record trades, notify

        # For safety: at development time we don't run live orders here unless you're ready.
        send_admin_alert("Arbitrage placeholder run", f"User {user['id']} ready for arbitrage (live execution disabled in code).")
    except Exception as e:
        logger.exception("execute_arbitrage_for_user error: %s", e)
        send_admin_alert("Arbitrage error", f"User {user.get('id')} — {e}")
