from binance.client import Client
from core.config import config
from utils.logger import wallet_logger, log_error
from datetime import datetime
import threading

class VirtualWallet:
    def __init__(self):
        self.client = Client(
            config.BINANCE_API_KEY,
            config.BINANCE_API_SECRET
        )
        self.wallets = {}
        self.lock = threading.Lock()
        wallet_logger.info("Virtual wallet system initialized")
        
    # ... باقي الدوال تبقى كما هي مع استخدام wallet_logger ...
