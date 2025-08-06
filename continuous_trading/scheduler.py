from celery import Celery
from core.config import Config
from binance.central_wallet import CentralWallet
import logging

app = Celery('scheduler', broker=os.getenv('REDIS_URL'))
logger = logging.getLogger(__name__)

@app.task
def execute_continuous_trade(user_id: str, amount: float):
    if not Config.validate_amount(amount):
        logger.error(f"Amount {amount} below minimum investment")
        return

    wallet = CentralWallet()
    if wallet.get_balance() < amount:
        logger.error("Insufficient central wallet balance")
        return

    # ... (تنفيذ الصفقة عبر Binance API)
