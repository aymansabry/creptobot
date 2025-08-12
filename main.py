import os
from dotenv import load_dotenv
from utils import create_exchange, place_market_order, place_sandbox_market_order, USE_SANDBOX
from database import get_setting

# تحميل متغيرات البيئة
load_dotenv()

# قراءة بيانات API من البيئة
EXCHANGE_NAME = get_setting("exchange_name", os.getenv("EXCHANGE_NAME", "binance"))
API_KEY = get_setting("api_key", os.getenv("API_KEY", ""))
API_SECRET = get_setting("api_secret", os.getenv("API_SECRET", ""))

# إنشاء الاتصال مع المنصة
exchange = create_exchange(EXCHANGE_NAME, API_KEY, API_SECRET, sandbox=USE_SANDBOX)

def run_trade(symbol, side, amount):
    if USE_SANDBOX:
        print("⚠️ التشغيل على وضع Sandbox (تجريبي)")
        return place_sandbox_market_order(exchange, symbol, side, amount)
    else:
        return place_market_order(exchange, symbol, side, amount)

if __name__ == "__main__":
    # مثال للتجربة
    trade_result = run_trade("BTC/USDT", "buy", 0.001)
    print("نتيجة الصفقة:", trade_result)
