import ccxt
import logging
from decimal import Decimal, ROUND_DOWN
import database

# إعداد اللوج
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# عمولة البوت (من قاعدة البيانات أو القيمة الافتراضية)
BOT_FEE_PERCENT = float(database.get_setting("bot_fee_percent", "10"))

# دالة لضبط الرقم حسب دقة المنصة
def adjust_amount(exchange, symbol, amount):
    market = exchange.market(symbol)
    precision = market['precision']['amount']
    return float(Decimal(amount).quantize(Decimal(10) ** -precision, rounding=ROUND_DOWN))

# إنشاء اتصال بالمنصة
def create_exchange(platform, api_key, api_secret, sandbox=False):
    if platform.lower() == "binance":
        exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': api_secret
        })
        if sandbox:
            exchange.set_sandbox_mode(True)
    elif platform.lower() == "kucoin":
        exchange = ccxt.kucoin({
            'apiKey': api_key,
            'secret': api_secret
        })
        if sandbox:
            exchange.urls['api'] = exchange.urls['test']
    else:
        raise ValueError("منصة غير مدعومة")
    return exchange

# التحقق من صحة API Keys
def validate_api_keys(platform, api_key, api_secret, sandbox=False):
    try:
        exchange = create_exchange(platform, api_key, api_secret, sandbox)
        balance = exchange.fetch_balance()
        logger.info(f"Balance fetched successfully from {platform}: {balance}")
        return True
    except Exception as e:
        logger.error(f"API Key validation failed for {platform}: {e}")
        return False

# تنفيذ أمر شراء/بيع
def execute_market_order(platform, api_key, api_secret, symbol, side, amount, sandbox=False):
    try:
        exchange = create_exchange(platform, api_key, api_secret, sandbox)
        amount_adj = adjust_amount(exchange, symbol, amount)
        order = exchange.create_market_order(symbol, side, amount_adj)
        logger.info(f"Executed {side} order: {order}")
        return order
    except Exception as e:
        logger.error(f"Failed to execute {side} order on {platform}: {e}")
        return None

# حساب الربح بعد العمولة
def calculate_net_profit(profit):
    fee = (BOT_FEE_PERCENT / 100) * profit
    return profit - fee

# فحص رصيد المستخدم
def check_investment_amount(platform, api_key, api_secret, symbol, required_amount, sandbox=False):
    try:
        exchange = create_exchange(platform, api_key, api_secret, sandbox)
        balance = exchange.fetch_balance()
        base_currency = symbol.split('/')[0]
        available = balance['free'].get(base_currency, 0)
        logger.info(f"Available balance for {base_currency} on {platform}: {available}")
        return available >= required_amount, available
    except Exception as e:
        logger.error(f"Error checking balance: {e}")
        return False, 0
