import ccxt
from openai import OpenAI
from config import OPENAI_API_KEY

def fetch_market_data():
    binance = ccxt.binance()
    tickers = binance.fetch_tickers()
    summary = {}

    for symbol in ["BTC/USDT", "ETH/USDT", "BNB/USDT"]:
        ticker = tickers.get(symbol)
        if ticker:
            summary[symbol] = {
                "price": ticker["last"],
                "change": ticker["percentage"]
            }

    return summary

def generate_ai_recommendations(data):
    client = OpenAI(api_key=OPENAI_API_KEY)
    prompt = f"""حلل لي حالة السوق بناءً على البيانات التالية:
{data}
وقدم نصائح استثمارية ذكية للمستخدم."""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content