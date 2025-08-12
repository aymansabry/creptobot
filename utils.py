# utils.py
import ccxt
from decimal import Decimal, ROUND_DOWN
import database

# جلب نسبة الربح من الإعدادات
BOT_FEE_PERCENT = float(database.get_setting("bot_fee_percent", "10"))

def validate_api_keys(platform, api_key, api_secret):
    """
    التحقق من صحة API keys للمنصة
    يعيد True إذا كانت صحيحة، أو False إذا كانت خاطئة
    """
    try:
        exchange_class = getattr(ccxt, platform)
        exchange = exchange_class({
            'apiKey': api_key,
            'secret': api_secret
        })
        # نحاول نجلب رصيد الحساب
        balance = exchange.fetch_balance()
        return True
    except Exception as e:
        print(f"API validation error for {platform}: {e}")
        return False

def get_precision_and_round(platform, symbol, amount):
    """
    إرجاع الكمية بعد التقريب حسب الـ precision للمنصة
    """
    try:
        exchange_class = getattr(ccxt, platform)
        exchange = exchange_class()
        markets = exchange.load_markets()
        precision = markets[symbol]['precision']['amount']
        rounded_amount = Decimal(amount).quantize(
            Decimal(str(10 ** -precision)), rounding=ROUND_DOWN
        )
        return float(rounded_amount)
    except Exception as e:
        print(f"Precision error: {e}")
        return amount

def execute_market_order(platform, api_key, api_secret, symbol, side, amount):
    """
    تنفيذ أمر سوق (Market Order) مع التقريب للـ precision
    """
    try:
        exchange_class = getattr(ccxt, platform)
        exchange = exchange_class({
            'apiKey': api_key,
            'secret': api_secret
        })
        amount = get_precision_and_round(platform, symbol, amount)
        order = exchange.create_market_order(symbol, side, amount)
        return order
    except Exception as e:
        print(f"Market order error: {e}")
        return None

def calculate_fee(profit):
    """حساب نسبة ربح البوت"""
    fee = (profit * BOT_FEE_PERCENT) / 100
    return round(fee, 8)
