from telegram import Update
from telegram.ext import CallbackContext
from services.arbitrage import find_arbitrage_opportunities
from services.execute import execute_arbitrage

def handle_run_arbitrage(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    # تحديد الأزواج التي سيتم تحليلها
    pairs = ['BTCUSDT', 'ETHUSDT', 'ETHBTC']
    opportunities = find_arbitrage_opportunities(pairs)

    if not opportunities:
        query.edit_message_text("❌ لا توجد فرص مراجحة مربحة حالياً.")
        return

    # اختيار أفضل فرصة
    best = opportunities[0]
    result = execute_arbitrage(best['path'], amount=100)

    # عرض النتائج للمستخدم
    query.edit_message_text(f"""
🔍 تم تنفيذ صفقة مراجحة:
- المسار: {result['path']}
- الربح: ${result['profit']}
- الرصيد النهائي: ${result['final']}
""")
