from tronpy import Tron
from tronpy.providers import HTTPProvider
from config import config

class TronManager:
    def __init__(self):
        self.client = Tron(
            provider=HTTPProvider(config.TRONGRID_API_URL),
            network='mainnet'
        )
        self.private_key = config.TRON_PRIVATE_KEY
    
    def send_usdt(self, to_address: str, amount: float):
        contract = self.client.get_contract(config.TRON_USDT_CONTRACT)
        txn = (
            contract.functions.transfer(to_address, int(amount * 10**6))
            .with_owner(config.ADMIN_WALLET)
            .fee_limit(10_000_000)
            .build()
            .sign(self.private_key)
        )
        return txn.broadcast()
