# market.py
import aiohttp
import json
import os
import openai
from typing import List

openai.api_key = os.getenv("OPENAI_API_KEY")  # قد يكون None إذا مش مفعّل

async def fetch_binance_24h() -> List[dict]:
    url = "https://api.binance.com/api/v3/ticker/24hr"
    async with aiohttp.ClientSession() as s:
        async with s.get(url, timeout=15) as r:
            return await r.json()

async def fetch_kucoin_tickers() -> List[dict]:
    url = "https://api.kucoin.com/api/v1/market/allTickers"
    async with aiohttp.ClientSession() as s:
        async with s.get(url, timeout=15) as r:
            j = await r.json()
            return j.get("data", {}).get("ticker", [])

async def analyze_market() -> str:
    """
    يجلب بيانات من Binance و KuCoin، يبني ملخصًا مختصرًا ويوجه طلب تحليل إلى OpenAI إن كان مفعلًا.
    يعيد نصًا جاهزًا للإرسال للمستخدم.
    """
    try:
        binance_raw = await fetch_binance_24h()
        kucoin_raw = await fetch_kucoin_tickers()

        # أبسط تصفية — أعلى 5 حسب حجم التداول (quoteVolume أو volValue)
        try:
            top_b = sorted(binance_raw, key=lambda x: float(x.get("quoteVolume", 0) or 0), reverse=True)[:5]
        except Exception:
            top_b = binance_raw[:5]

        summary_lines = ["📊 **حالة السوق الآن (تلخيص مختصر):**", "🔥 أشهر العملات على Binance:"]
        for t in top_b:
            symbol = t.get("symbol")
            change = t.get("priceChangePercent", "0")
            last = t.get("lastPrice") or t.get("last") or ""
            summary_lines.append(f"• {symbol} — {change}% — {last}$")

        summary_lines.append("\n(مصدر البيانات: Binance و KuCoin)")

        # طلب تحليل من OpenAI إن كان مفتاح مفعل
        if openai.api_key:
            prompt = (
                "أعطني تحليلًا موجزًا باللغة العربية عن حالة سوق العملات الرقمية الآن "
                "(اعتمادًا على أعلى 5 عملات حسب الحجم من Binance). "
                "اذكر نقاط القوة/الضعف، مؤشرات سريعة، واقتراحات فرص مراجحة أو مضاربة قصيرة المدى."
                f"\n\nبيانات Binance top: {json.dumps(top_b, ensure_ascii=False)}"
            )
            try:
                resp = await openai.ChatCompletion.acreate(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=400,
                    temperature=0.7
                )
                ai_text = resp.choices[0].message.content
                summary_lines.append("\n🤖 اقتراحات وتحليل (OpenAI):")
                summary_lines.append(ai_text)
            except Exception as e:
                summary_lines.append(f"\n⚠️ حدث خطأ أثناء تحليل OpenAI: {e}")

        else:
            summary_lines.append("\nℹ️ OpenAI غير مفعّل — لتفعيل تحليلات متقدمة ضع OPENAI_API_KEY في المتغيرات البيئية.")

        return "\n".join(summary_lines)

    except Exception as e:
        return f"حدث خطأ أثناء جلب أو تحليل بيانات السوق: {e}"

async def suggest_trades() -> str:
    """
    يطلب من OpenAI اقتراحات صفقات/مراجحة. يرجى تفعيل OPENAI_API_KEY.
    """
    if not openai.api_key:
        return "OpenAI غير مفعّل. ضع OPENAI_API_KEY في متغيرات البيئة لتفعيل الاقتراحات."

    prompt = (
        "اقترح فرص مراجحة أو مضاربة قصيرة المدى بين منصتي Binance و KuCoin. "
        "اشرح خطوات التنفيذ، المخاطر المحتملة، وحساب تقريبي للربح/الخسارة. اكتب بالعربية."
    )
    try:
        resp = await openai.ChatCompletion.acreate(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=350,
            temperature=0.8
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"حدث خطأ أثناء طلب الاقتراحات من OpenAI: {e}"
