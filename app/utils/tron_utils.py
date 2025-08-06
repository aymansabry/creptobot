import os
from tronpy import Tron
from tronpy.providers import HTTPProvider

TRON_PRIVATE_KEY = os.getenv("TRON_PRIVATE_KEY")
TRON_API = HTTPProvider(api_key=os.getenv("TRON_API_KEY"))
TRON_CLIENT = Tron(provider=TRON_API)

OWNER_ADDRESS = os.getenv("TRON_OWNER_ADDRESS")

def send_trx(to_address: str, amount: float):
    txn = (
        TRON_CLIENT.trx.transfer(OWNER_ADDRESS, to_address, int(amount * 1_000_000))
        .memo("Bot Profit Share")
        .build()
        .sign(TRON_PRIVATE_KEY)
    )
    result = txn.broadcast().wait()
    return result["id"]
