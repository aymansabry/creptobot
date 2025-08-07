from services.binance_service import place_order, get_balance
from services.tron_service import send_usdt
from services.ai_analysis import analyze_market
from database.crud import record_profit
from constants import BOT_COMMISSION

async def execute_manual_deal(user_id, amount):
    # 1. تحليل السوق
    prompt = f"لدي {amount} USDT، ابحث عن صفقة آمنة بربح لا يقل عن 3%."
    analysis = analyze_market(prompt)

    # 2. تنفيذ صفقة وهمية على Binance (افتراضيًا MARKET)
    order = place_order("BTCUSDT", "BUY", quantity=amount / 30000)  # مثال بسيط

    # 3. خصم العمولة
    commission = amount * BOT_COMMISSION / 100
    profit = amount * 0.03  # ضمان 3%
    send_usdt(to_address="عميل", amount=(amount + profit - commission))
    send_usdt(to_address="مدير", amount=commission)

    # 4. تسجيل الصفقة
    await record_profit(user_id, profit, commission)

    return f"تم تنفيذ الصفقة بنجاح ✅\nربحك: {profit} USDT"
