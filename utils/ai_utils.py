# utils/ai_utils.py

import openai
from config.config import Config

openai.api_key = Config.OPENAI_API_KEY

async def analyze_market():
    prompt = "Give me 3 arbitrage opportunities in USDT crypto trading between global exchanges."
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response['choices'][0]['message']['content']
