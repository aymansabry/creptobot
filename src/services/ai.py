import random

async def suggest_deals() -> str:
    # صفقات وهمية كمثال
    fake_deals = [
        {"coin": "BTC/USDT", "buy": 29700, "sell": 30600},
        {"coin": "ETH/USDT", "buy": 1800, "sell": 1880},
        {"coin": "SOL/USDT", "buy": 22, "sell": 23.5},
    ]
    result = ""
    for d in fake_deals:
        profit = ((d["sell"] - d["buy"]) / d["buy"]) * 100
        if profit < 3:
            continue  # رفض الصفقات بدون ربح ≥ 3%
        result += f"🔹 {d['coin']}\n🟢 شراء: {d['buy']}$\n🔴 بيع: {d['sell']}$\n💰 ربح متوقع: {profit:.2f}%\n\n"
    return result if result else "لا توجد صفقات مربحة حالياً."
