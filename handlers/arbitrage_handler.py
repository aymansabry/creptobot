from services.arbitrage import find_arbitrage_opportunities
from services.execute import execute_arbitrage

def handle_arbitrage(update, context):
    pairs = ['BTCUSDT', 'ETHUSDT', 'ETHBTC']
    opportunities = find_arbitrage_opportunities(pairs)

    if not opportunities:
        update.message.reply_text("لا توجد فرص مراجحة مربحة حاليًا.")
        return

    best = opportunities[0]
    result = execute_arbitrage(best['path'], amount=100)

    update.message.reply_text(f"""
🚀 تم تنفيذ صفقة مراجحة:
- المسار: {result['path']}
- الربح: ${result['profit']}
- الرصيد النهائي: ${result['final']}
""")
