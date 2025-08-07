from tronpy import Tron
from tronpy.providers import HTTPProvider
from config import TRON_API_KEY, TRON_MANAGER_WALLET, TRON_MANAGER_PRIVATE_KEY
from logger import logger

client = Tron(HTTPProvider(api_key=TRON_API_KEY))

def send_usdt(to_address, amount):
    try:
        txn = (
            client.get_contract('TXLAQ63Xg1NAzckPwKHvzw7CSEmLMEqcdj')
            .functions.transfer(to_address, int(amount * 1_000_000))
            .with_owner(TRON_MANAGER_WALLET)
            .fee_limit(2_000_000)
            .build()
            .sign(PRIVATE_KEY=TRON_MANAGER_PRIVATE_KEY)
        )
        result = txn.broadcast().wait()
        logger.info(f"TRON Transfer Success: {result}")
        return result['id']
    except Exception as e:
        logger.error(f"TRON Transfer Error: {e}")
        return None
