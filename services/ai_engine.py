# project_root/services/ai_engine.py

from core.config import settings
import openai
import json

class AIEngine:
    """
    AI Engine for generating trading signals using OpenAI's API.
    """
    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY
        self.model = "gpt-3.5-turbo"

    async def generate_signal(self, market_data: dict, strategy: str) -> dict:
        """
        Generates a trading signal (buy/sell) based on real-time market data.
        """
        prompt = self._build_prompt(market_data, strategy)
        
        response = await openai.ChatCompletion.acreate(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a specialized trading bot AI. You analyze market data and provide precise trading signals in a JSON format."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        
        ai_response_text = response.choices[0].message.content
        return self._parse_ai_response(ai_response_text)
    
    def _build_prompt(self, market_data: dict, strategy: str) -> str:
        """Constructs a detailed prompt for the AI."""
        if strategy == "arbitrage":
            return (
                f"Analyze the following data for an arbitrage opportunity:\n"
                f"Binance Price: {market_data.get('binance_price')}\n"
                f"KuCoin Price: {market_data.get('kucoin_price')}\n"
                f"What is the best action (buy/sell), on which exchange, for which currency, and what amount should be used to minimize risk and maximize profit? Provide the output in a JSON-like format with keys: action, symbol, exchange, amount, reason."
            )
        elif strategy == "spot":
            return (
                f"Analyze the following real-time market data for a spot trading opportunity:\n"
                f"Symbol: {market_data.get('symbol')}\n"
                f"Current Price: {market_data.get('price')}\n"
                f"Volume (24h): {market_data.get('volume_24h')}\n"
                f"RSI: {market_data.get('rsi')}\n"
                f"MACD: {market_data.get('macd')}\n"
                f"Sentiment: {market_data.get('sentiment')}\n"
                f"Should I buy or sell this currency? What is the recommended amount to invest? Provide the output in a JSON format with keys: action, symbol, amount, reason."
            )
        
        return "No strategy specified."

    def _parse_ai_response(self, text: str) -> dict:
        """Parses the AI's string response into a dictionary."""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            print(f"Warning: AI response was not valid JSON. Response: {text}")
            return {"action": "hold", "reason": "Could not parse AI response."}
