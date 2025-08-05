# app/services/openai.py
import os
import openai
openai.api_key = os.getenv("OPENAI_API_KEY")

async def summarize_message(message: str) -> str:
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": message}
        ]
    )
    return response['choices'][0]['message']['content']
