# project_root/services/ai_engine.py

import openai
from core.config import settings
import json
import random
import re

class AIEngine:
    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY
        self.model = "gpt-3.5-turbo" # Can be updated to gpt-4 if you have access

    async def get_trade_recommendation(self):
        """
        Generates a list of AI-powered trade recommendations using ChatGPT.
        The output is a structured JSON array for easy parsing.
        """
        
        prompt = (
            "You are an AI-powered crypto trading assistant. Generate a list of 5 unique trading recommendations "
            "for a user. For each recommendation, provide the following structured data as a JSON array:\n"
            "1. `code`: A unique trade code starting with 'AI-'.\n"
            "2. `symbol`: A trading pair from this list: BTC/USDT, ETH/USDT, SOL/USDT, XRP/USDT.\n"
            "3. `exchange`: An exchange from this list: binance, kucoin.\n"
            "4. `potential_profit`: A random percentage between 2.0% and 8.0%.\n"
            "5. `duration_minutes`: A random duration in minutes between 30 and 120.\n"
            "6. `entry_strategy`: A brief, one-sentence description of the entry strategy.\n"
            "7. `exit_strategy`: A brief, one-sentence description of the exit strategy.\n"
            "The output must be a valid JSON array, with no extra text or explanations before or after the JSON."
        )

        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that provides JSON output."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )

            # Extract and clean the JSON string from the response
            recommendations_json = response.choices[0].message.content.strip()
            
            # The AI might add backticks, so we'll remove them to ensure valid JSON
            clean_json = re.sub(r'```json\n|\n```', '', recommendations_json)
            
            recommendations = json.loads(clean_json)

            # Add static data like commission rates and fees
            commission_rate = 0.05
            exchange_fees = 0.001
            for rec in recommendations:
                rec['commission_rate'] = commission_rate
                rec['exchange_fees'] = exchange_fees
            
            return recommendations

        except Exception as e:
            print(f"Error communicating with ChatGPT API: {e}")
            return []
