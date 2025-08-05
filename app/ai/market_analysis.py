# app/ai/market_analysis.py
import openai
import os
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

async def analyze_market(prices: list) -> dict:
    prompt = (
        "لديك قائمة بأسعار العملات الرقمية من منصات مختلفة. "
        "حلل البيانات واقترح أفضل صفقة يمكن تنفيذها لتحقيق ربح. "
        "يجب أن تتضمن الإجابة اسم العملة والمنصة المقترحة للشراء والمنصة المقترحة للبيع ونسبة الربح."
        f"\n\nالأسعار:\n{prices}"
    )

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "أنت مساعد خبير في تداول العملات الرقمية."},
            {"role": "user", "content": prompt}
        ]
    )

    message = response.choices[0].message.content.strip()
    return parse_response(message)


def parse_response(response_text: str) -> dict:
    lines = response_text.split('\n')
    result = {}

    for line in lines:
        if ':' in line:
            key, value = line.split(':', 1)
            result[key.strip()] = value.strip()

    return result
