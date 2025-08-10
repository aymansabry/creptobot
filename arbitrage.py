import ccxt
import time
from settings import EXCHANGES, MIN_PROFIT_PERCENT, OWNER_ID
from utils import send_alert

def get_exchange_instance(name, api_key, api_secret):
    """إنشاء اتصال بالمنصة"""
    try:
        exchange_class = getattr(ccxt, name)
        exchange = exchange_class({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True
        })
        return exchange
    except Exception as e:
        send_alert(f"❌ خطأ في إنشاء اتصال بـ {name}: {str(e)}", OWNER_ID)
        return None

def get_price(exchange, symbol):
    """الحصول على سعر العملة"""
    try:
        ticker = exchange.fetch_ticker(symbol)
        return ticker['last']
    except Exception as e:
        return None

def find_arbitrage_opportunities():
    """البحث عن فرص المراجحة"""
    opportunities = []
    for sym in EXCHANGES['symbols']:
        prices = {}
        for ex_name, creds in EXCHANGES['accounts'].items():
            exchange = get_exchange_instance(ex_name, creds['apiKey'], creds['secret'])
            if not exchange:
                continue
            price = get_price(exchange, sym)
            if price:
                prices[ex_name] = price

        if len(prices) > 1:
            max_ex = max(prices, key=prices.get)
            min_ex = min(prices, key=prices.get)
            profit_percent = ((prices[max_ex] - prices[min_ex]) / prices[min_ex]) * 100

            if profit_percent >= MIN_PROFIT_PERCENT:
                opportunities.append({
                    'symbol': sym,
                    'buy_from': min_ex,
                    'sell_to': max_ex,
                    'profit_percent': profit_percent
                })

    return opportunities

def execute_arbitrage():
    """تنفيذ عمليات المراجحة"""
    ops = find_arbitrage_opportunities()
    if not ops:
        return

    for op in ops:
        send_alert(
            f"💹 فرصة مراجحة:\n"
            f"العملة: {op['symbol']}\n"
            f"اشترِ من: {op['buy_from']}\n"
            f"بع في: {op['sell_to']}\n"
            f"الربح المتوقع: {op['profit_percent']:.2f}%",
            OWNER_ID
        )

        # تنفيذ الصفقة (شراء ثم بيع)
        # يمكن إضافة حماية من الخسائر ووقف التنفيذ في حالة تغير السعر
        try:
            buy_ex = get_exchange_instance(op['buy_from'], **EXCHANGES['accounts'][op['buy_from']])
            sell_ex = get_exchange_instance(op['sell_to'], **EXCHANGES['accounts'][op['sell_to']])

            # تنفيذ أمر شراء (هنا مثال بسيط)
            buy_ex.create_market_buy_order(op['symbol'], 1)

            # تنفيذ أمر بيع
            sell_ex.create_market_sell_order(op['symbol'], 1)

            send_alert(f"✅ تم تنفيذ المراجحة بنجاح: {op['symbol']}", OWNER_ID)
        except Exception as e:
            send_alert(f"❌ فشل تنفيذ المراجحة: {str(e)}", OWNER_ID)

if __name__ == "__main__":
    while True:
        execute_arbitrage()
        time.sleep(10)  # فاصل بين المحاولات