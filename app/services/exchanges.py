# app/services/exchange.py
import os
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

class ExchangeService:

    @staticmethod
    async def analyze_opportunities():
        prompt = "حلل فرص التداول بين المنصات المختلفة لتحقيق أرباح آمنة"
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "أنت خبير في تحليل أسعار العملات الرقمية"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5
        )
        return response.choices[0].message.content.strip()
