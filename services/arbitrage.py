import ccxt
from db import get_user_exchanges, get_user_wallet, log_arbitrage, update_wallet
from utils import calculate_profit, check_balance, get_fee

def execute_arbitrage(user_id):
    exchanges = get_user_exchanges(user_id)
    wallet = get_user_wallet(user_id)

    opportunity = find_best_opportunity(exchanges)
    if not opportunity:
        return "لا توجد فرصة مناسبة الآن"

    symbol = opportunity['symbol']
    amount = opportunity['amount']
    buy_ex = exchanges[opportunity['buy_exchange']]
    sell_ex = exchanges[opportunity['sell_exchange']]

    # تحقق من الرصيد
    if not check_balance(buy_ex, symbol, amount, side='BUY') or not check_balance(sell_ex, symbol, amount, side='SELL'):
        return "الرصيد غير كافي لتنفيذ الصفقة"

    # تنفيذ أوامر السوق
    try:
        buy_order = buy_ex.create_market_buy_order(symbol, amount)
        sell_order = sell_ex.create_market_sell_order(symbol, amount)
    except Exception as e:
        return f"فشل في تنفيذ الأوامر: {str(e)}"

    # حساب الربح الصافي
    buy_price = buy_order['average']
    sell_price = sell_order['average']
    fee = get_fee(buy_order, sell_order)
    profit = calculate_profit(buy_price, sell_price, amount) - fee

    # تسجيل الصفقة
    log_arbitrage(user_id, opportunity, profit)

    # تحديث المحفظة
    update_wallet(user_id, profit)

    return f"✅ تم تنفيذ الصفقة بنجاح وربح {profit:.2f} USDT"