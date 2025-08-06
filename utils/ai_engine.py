import openai
from config.config import settings

openai.api_key = settings.AI_API_KEY

async def ask_ai(prompt: str) -> str:
    response = openai.ChatCompletion.create(
        model=settings.OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()
