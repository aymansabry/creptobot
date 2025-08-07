import openai
from config import OPENAI_API_KEY
openai.api_key = OPENAI_API_KEY

def analyze_market(prompt_text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "أنت محلل مالي محترف تبحث عن فرص آمنة."},
                {"role": "user", "content": prompt_text}
            ],
            max_tokens=400
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        return f"❌ خطأ في تحليل السوق: {e}"
