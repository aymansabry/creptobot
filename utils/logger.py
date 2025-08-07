import logging
from datetime import datetime

def setup_logger():
    logging.basicConfig(
        filename=f'logs/bot_{datetime.now().date()}.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def log_trade(trade_data: dict):
    logging.info(f"Trade executed: {trade_data}")
