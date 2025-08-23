import os
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

class AIStrategy:
    def analyze(self, market_data):
        try:
            prompt = f"حلل لي وضع سوق الكريبتو بناءً على البيانات: {market_data}"
            response = openai.Completion.create(
                model="gpt-4o-mini",
                prompt=prompt,
                max_tokens=150
            )
            return response.choices[0].text.strip()
        except Exception as e:
            return f"⚠️ خطأ في تحليل السوق: {e}"
