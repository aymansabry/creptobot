import os
from dotenv import load_dotenv
from typing import Dict, Any

load_dotenv()

class Config:
    # Binance API Configuration
    BINANCE_API_KEY: str = os.getenv('BINANCE_API_KEY', '')
    BINANCE_API_SECRET: str = os.getenv('BINANCE_API_SECRET', '')
    BINANCE_DEPOSIT_ADDRESS: str = os.getenv('BINANCE_DEPOSIT_ADDRESS', '')
    
    # Trading Parameters
    MIN_TRADE_AMOUNT: float = float(os.getenv('MIN_TRADE_AMOUNT', 1.0))  # 1 USDT minimum
    MAX_TRADE_AMOUNT: float = float(os.getenv('MAX_TRADE_AMOUNT', 10000.0))
    COMMISSION_RATE: float = float(os.getenv('COMMISSION_RATE', 0.001))  # 0.1%
    
    # Virtual Wallet Settings
    MIN_DEPOSIT: float = float(os.getenv('MIN_DEPOSIT', 10.0))
    WALLET_AUTO_CHECK_INTERVAL: int = int(os.getenv('WALLET_CHECK_INTERVAL', 300))  # 5 minutes
    
    # Risk Management
    MAX_DAILY_LOSS_PERCENT: float = float(os.getenv('MAX_DAILY_LOSS', 5.0))  # 5%
    MAX_RISK_LEVEL: int = int(os.getenv('MAX_RISK_LEVEL', 3))  # 1-5 scale
    
    # System Mode
    DEMO_MODE: bool = os.getenv('DEMO_MODE', 'False').lower() == 'true'
    MAINTENANCE_MODE: bool = os.getenv('MAINTENANCE_MODE', 'False').lower() == 'true'
    
    # Telegram
    ADMIN_IDS: list = [int(id) for id in os.getenv('ADMIN_IDS', '').split(',') if id]
    
    @property
    def trading_pairs(self) -> Dict[str, Any]:
        return {
            'BTCUSDT': {'min_qty': 0.00001, 'price_precision': 1},
            'ETHUSDT': {'min_qty': 0.001, 'price_precision': 2},
            'BNBUSDT': {'min_qty': 0.01, 'price_precision': 2}
        }

config = Config()
