import os
from binance.client import Client
from binance.enums import *

BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY")
USDT_ADDRESS = os.getenv("BINANCE_USDT_ADDRESS")  # عنوان المحفظة المركزية

client = Client(BINANCE_API_KEY, BINANCE_SECRET_KEY)

def check_deposit(user_address: str, amount_threshold: float):
    """
    التحقق مما إذا تم الإيداع من المستخدم بعنوانه الخاص
    """
    deposits = client.get_deposit_history(asset='USDT')
    for dep in deposits:
        if dep['address'] == user_address and dep['amount'] >= amount_threshold and dep['status'] == 1:
            return True
    return False

def get_binance_balance():
    """
    جلب رصيد USDT في المحفظة المركزية
    """
    balance = client.get_asset_balance(asset='USDT')
    return float(balance['free'])
