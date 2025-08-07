import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Binance API
    BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
    BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET')
    
    # Trading Parameters
    MAX_TRADE_AMOUNT = float(os.getenv('MAX_TRADE_AMOUNT', 10000))
    MIN_TRADE_AMOUNT = float(os.getenv('MIN_TRADE_AMOUNT', 1))
    COMMISSION_RATE = float(os.getenv('COMMISSION_RATE', 0.001))
    
    # Risk Management
    DAILY_LOSS_LIMIT = float(os.getenv('DAILY_LOSS_LIMIT', -500))
    MAX_RISK_LEVEL = int(os.getenv('MAX_RISK_LEVEL', 3))
    
    # AI Settings
    AI_CONFIDENCE_THRESHOLD = float(os.getenv('AI_CONFIDENCE_THRESHOLD', 0.85))

config = Config()
