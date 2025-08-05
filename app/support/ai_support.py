# app/support/ai_support.py
import openai
import os
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")


async def ai_customer_support(message: str) -> str:
    prompt = (
        "أنت موظف دعم فني ذكي لبوت تداول العملات الرقمية. "
        "رد على استفسارات العملاء بشكل واضح ومهذب. "
        "إذا كان السؤال يتطلب تدخل بشري، اشرح له أنه سيتم تحويله لموظف الدعم البشري.\n"
        f"سؤال العميل:\n{message}"
    )

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "أنت مساعد دعم فني محترف."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content.strip()
