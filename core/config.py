import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # إعدادات التداول
    MIN_INVESTMENT = float(os.getenv('MIN_INVESTMENT', 1.0))  # الحد الأدنى 1 USDT
    TRADING_MODE = os.getenv('TRADING_MODE', 'virtual')  # virtual/real
    
    # إعدادات بينانس
    BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
    BINANCE_SECRET = os.getenv('BINANCE_SECRET')
    
    # إعدادات الذكاء الاصطناعي
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    AI_MODEL = os.getenv('AI_MODEL', 'gpt-4')

    @staticmethod
    def validate_amount(amount: float) -> bool:
        return amount >= Config.MIN_INVESTMENT
