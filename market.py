import aiohttp
import os
import json
import openai
from datetime import datetime

openai.api_key = os.getenv("OPENAI_API_KEY")

async def fetch_binance_data():
    url = "https://api.binance.com/api/v3/ticker/24hr"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.json()

async def fetch_kucoin_data():
    url = "https://api.kucoin.com/api/v1/market/allTickers"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            return data.get("data", {}).get("ticker", [])

async def analyze_market():
    # 1- جلب بيانات السوق من Binance و KuCoin
    binance_data, kucoin_data = await fetch_binance_data(), await fetch_kucoin_data()

    # 2- تصفية العملات الأكثر نشاطاً
    top_binance = sorted(binance_data, key=lambda x: float(x['quoteVolume']), reverse=True)[:5]
    top_kucoin = sorted(kucoin_data, key=lambda x: float(x['volValue']), reverse=True)[:5]

    # 3- تجهيز ملخص السوق
    market_summary = "📊 **حالة السوق الآن**\n"
    market_summary += "🔥 أشهر العملات على Binance:\n"
    for c in top_binance:
        market_summary += f"• {c['symbol']}: {c['priceChangePercent']}% ({c['lastPrice']}$)\n"

    market_summary += "\n💎 أشهر العملات على KuCoin:\n"
    for c in top_kucoin:
        market_summary += f"• {c['symbol']}: {c['changeRate']} ({c['last']}$)\n"

    # 4- استدعاء الذكاء الاصطناعي لاقتراح فرص
    prompt = f"""
    هذه بيانات السوق للعملات الرقمية:
    Binance: {json.dumps(top_binance, ensure_ascii=False)}
    KuCoin: {json.dumps(top_kucoin, ensure_ascii=False)}

    حلل السوق واقترح أفضل فرص الاستثمار السريعة مع أسباب واضحة.
    """

    try:
        ai_response = await openai.ChatCompletion.acreate(
            model="gpt-4",
            messages=[{"role": "system", "content": "أنت خبير تداول عملات رقمية."},
                      {"role": "user", "content": prompt}],
            temperature=0.7
        )
        suggestions = ai_response.choices[0].message["content"]
        market_summary += f"\n🤖 **اقتراحات الذكاء الاصطناعي:**\n{suggestions}"
    except Exception as e:
        market_summary += f"\n⚠️ لم نتمكن من جلب اقتراحات الذكاء الاصطناعي: {e}"

    return market_summary
