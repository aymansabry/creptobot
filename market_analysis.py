# market_analysis.py
import ccxt
import statistics
import database
import utils

def get_market_summary():
    """
    تحليل السوق بناءً على متوسطات الحركة وبعض المؤشرات البسيطة.
    """
    try:
        # المنصات المدعومة
        exchanges = ["binance", "kucoin", "bybit"]
        summary = "📊 **تحليل السوق الحالي:**\n\n"

        for ex_name in exchanges:
            api_data = database.get_api_keys_for_exchange(ex_name)
            if not api_data:
                continue

            api_key, api_secret = api_data
            exchange = utils.get_exchange(ex_name, api_key, api_secret)

            # اختيار زوج عملة شهير للتحليل
            symbol = "BTC/USDT"
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe="1h", limit=50)
            closes = [c[4] for c in ohlcv]  # أسعار الإغلاق

            # حساب المتوسط المتحرك البسيط
            sma_20 = statistics.mean(closes[-20:])
            last_price = closes[-1]

            # الاتجاه العام
            if last_price > sma_20:
                trend = "📈 صاعد"
            elif last_price < sma_20:
                trend = "📉 هابط"
            else:
                trend = "➖ عرضي"

            summary += f"📌 {ex_name.upper()} - {symbol}\n"
            summary += f"السعر الحالي: {last_price:.2f} USDT\n"
            summary += f"المتوسط المتحرك 20 ساعة: {sma_20:.2f} USDT\n"
            summary += f"الاتجاه: {trend}\n\n"

        if summary.strip() == "":
            return "⚠️ لا توجد بيانات منصات متصلة للتحليل."

        return summary

    except Exception as e:
        return f"❌ خطأ في تحليل السوق: {e}"
