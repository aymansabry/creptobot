from tronpy import Tron
from tronpy.keys import PrivateKey
import os

TRON_PRIVATE_KEY = os.getenv("TRON_PRIVATE_KEY")
TRON_ADDRESS = os.getenv("TRON_TARGET_ADDRESS")  # عنوان محفظة المدير
TRON_CLIENT = Tron()

def send_commission(amount_usdt: float):
    """
    إرسال العمولة إلى محفظة TRON الخاصة بالمالك
    """
    priv_key = PrivateKey(bytes.fromhex(TRON_PRIVATE_KEY))
    usdt_contract = TRON_CLIENT.get_contract('TXLAQ63Xg1NAzckPwKHvzw7CSEmLMEqcdj')  # عقد USDT الرسمي

    txn = (
        usdt_contract.functions.transfer(TRON_ADDRESS, int(amount_usdt * 1_000_000))
        .with_owner(priv_key.public_key.to_base58check_address())
        .fee_limit(1_000_000)
        .build()
        .sign(priv_key)
    )
    result = txn.broadcast().wait()
    return result['id']
