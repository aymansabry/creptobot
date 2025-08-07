import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

async def suggest_best_trades(prices: dict, min_profit: float = 3.0):
    """
    تحليل الأسعار بين المنصات واختيار أفضل فرص الأرباح
    """
    prompt = f"""
المهمة: تحليل فروقات الأسعار بين منصات التداول المختلفة للعملة USDT، واقتراح صفقات آمنة لا تقل نسبة الربح فيها عن {min_profit}٪ بعد خصم الرسوم.

البيانات: {prices}

المخرجات المطلوبة:
- اسم المنصة للشراء
- اسم المنصة للبيع
- سعر الشراء
- سعر البيع
- نسبة الربح
- سبب الاختيار (بشكل مختصر)
- هل الصفقة آمنة

الرد باللغة العربية وبشكل منظم وواضح.
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ خطأ في تحليل الذكاء الاصطناعي: {e}"
