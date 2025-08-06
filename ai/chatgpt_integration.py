import openai
from core.config import Config

openai.api_key = Config.OPENAI_API_KEY

class AITradingAdvisor:
    @staticmethod
    def analyze_market(market_data: dict) -> dict:
        prompt = f"""
        Analyze this crypto market data for arbitrage opportunities:
        {market_data}
        Provide your recommendation in JSON format with:
        - opportunity (bool)
        - suggested_action (buy/sell/hold)
        - confidence (0-100)
        - best_pair (str)
        """
        
        response = openai.ChatCompletion.create(
            model=Config.AI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        try:
            return eval(response.choices[0].message.content)
        except:
            return {
                "opportunity": False,
                "suggested_action": "hold",
                "confidence": 0,
                "best_pair": "N/A"
            }
