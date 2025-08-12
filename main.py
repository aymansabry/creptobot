import os
import logging
from dotenv import load_dotenv
from database import get_setting, init_db
from utils import (
    create_exchange,
    place_market_order,
    place_sandbox_market_order,
    USE_SANDBOX
)

# إعدادات اللوج
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# تحميل متغيرات البيئة
load_dotenv()

def main():
    # تهيئة قاعدة البيانات
    init_db()

    # قراءة الإعدادات من قاعدة البيانات أو من .env
    exchange_name = get_setting("exchange_name", os.getenv("EXCHANGE_NAME", "binance"))
    api_key = get_setting("api_key", os.getenv("API_KEY", ""))
    api_secret = get_setting("api_secret", os.getenv("API_SECRET", ""))

    if not api_key or not api_secret:
        logging.error("❌ لم يتم إدخال API Key أو API Secret. يرجى ضبط الإعدادات أولاً.")
        return

    # إنشاء الاتصال مع المنصة
    exchange = create_exchange(exchange_name, api_key, api_secret, sandbox=USE_SANDBOX)

    # مثال لتنفيذ أمر
    symbol = get_setting("trade_symbol", os.getenv("TRADE_SYMBOL", "BTC/USDT"))
    side = get_setting("trade_side", os.getenv("TRADE_SIDE", "buy"))
    amount = float(get_setting("trade_amount", os.getenv("TRADE_AMOUNT", "0.001")))

    if USE_SANDBOX:
        logging.info("⚠️ التشغيل على وضع Sandbox (تجريبي)")
        result = place_sandbox_market_order(exchange, symbol, side, amount)
    else:
        logging.info("🚀 تنفيذ أمر حقيقي في السوق")
        result = place_market_order(exchange, symbol, side, amount)

    logging.info(f"نتيجة الصفقة: {result}")

if __name__ == "__main__":
    main()
