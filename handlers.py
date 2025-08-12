import logging
import utils
import database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# بدء استثمار جديد
def start_investment(user_id, platform, api_key, api_secret, symbol, amount, sandbox=False):
    # التحقق من API Keys
    if not utils.validate_api_keys(platform, api_key, api_secret, sandbox):
        return {"status": "error", "message": "مفاتيح API غير صالحة"}

    # فحص الرصيد
    has_balance, available = utils.check_investment_amount(platform, api_key, api_secret, symbol, amount, sandbox)
    if not has_balance:
        return {"status": "error", "message": f"الرصيد غير كافي. المتاح: {available}"}

    # تنفيذ أمر شراء
    order = utils.execute_market_order(platform, api_key, api_secret, symbol, "buy", amount, sandbox)
    if not order:
        return {"status": "error", "message": "فشل تنفيذ أمر الشراء"}

    # حفظ الصفقة في قاعدة البيانات
    database.save_trade(user_id, platform, symbol, amount, "buy", order)
    return {"status": "success", "message": "تم بدء الاستثمار بنجاح", "order": order}

# إنهاء استثمار
def end_investment(user_id, platform, api_key, api_secret, symbol, amount, sandbox=False):
    # تنفيذ أمر بيع
    order = utils.execute_market_order(platform, api_key, api_secret, symbol, "sell", amount, sandbox)
    if not order:
        return {"status": "error", "message": "فشل تنفيذ أمر البيع"}

    # حساب الربح بعد العمولة
    profit = calculate_profit(user_id, symbol)  # هتكون دالة في database أو utils
    net_profit = utils.calculate_net_profit(profit)

    # تحديث الصفقة في قاعدة البيانات
    database.update_trade(user_id, symbol, "sell", order, profit, net_profit)

    return {
        "status": "success",
        "message": "تم إنهاء الاستثمار بنجاح",
        "order": order,
        "profit": profit,
        "net_profit": net_profit
    }

# عرض سجل الصفقات
def get_trade_history(user_id):
    trades = database.get_user_trades(user_id)
    return {"status": "success", "trades": trades}
