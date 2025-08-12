# main.py
import os
from utils import get_exchange, execute_market_order, log_message, save_trade, calculate_profit_with_fee
from database import get_setting
from datetime import datetime

def main():
    log_message("🚀 Bot started")

    # قراءة إعدادات أساسية من قاعدة البيانات
    exchange_name = get_setting("exchange_name", "binance")
    api_key = get_setting("api_key", "")
    api_secret = get_setting("api_secret", "")
    symbol = get_setting("trade_symbol", "BTC/USDT")
    trade_side = get_setting("trade_side", "buy").lower()  # buy or sell
    trade_amount = float(get_setting("trade_amount", "0.001"))

    # تجهيز المنصة
    try:
        exchange = get_exchange(exchange_name, api_key, api_secret)
        log_message(f"✅ Connected to {exchange_name} (sandbox={get_setting('use_sandbox', 'false')})")
    except Exception as e:
        log_message(f"❌ Error connecting to exchange: {e}")
        return

    # تنفيذ الصفقة
    try:
        order = execute_market_order(exchange, symbol, trade_side, trade_amount)
        log_message(f"📌 Order executed: {order}")

        # حساب الربح (افتراضيًا نعتبر ربح وهمي للتجربة)
        fake_profit = 50.0  # قيمة تجريبية
        net_profit = calculate_profit_with_fee(fake_profit)
        save_trade(1, exchange_name, symbol, trade_side, order['price'] if 'price' in order else 0, trade_amount, net_profit)
        log_message(f"💰 Net profit after fee: {net_profit}")

    except Exception as e:
        log_message(f"❌ Error executing order: {e}")

if __name__ == "__main__":
    main()
