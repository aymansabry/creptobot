from ai.chatgpt_integration import AITradingAdvisor

class RiskManager:
    @staticmethod
    def approve_trade(trade_data: dict) -> bool:
        analysis = AITradingAdvisor.analyze_market(trade_data)
        return analysis['confidence'] >= 80 and analysis['opportunity']
