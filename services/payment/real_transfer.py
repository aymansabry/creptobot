from tronpy import Tron
from tronpy.providers import HTTPProvider
from config import config

class TronPayment:
    def __init__(self):
        self.client = Tron(
            provider=HTTPProvider(endpoint_uri="https://api.trongrid.io"),
            network='mainnet'
        )
        self.private_key = config.TRON_PRIVATE_KEY
        
    async def send_usdt(self, to_address: str, amount: float):
        contract = self.client.get_contract("TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t")
        txn = (
            contract.functions.transfer(to_address, int(amount * 10**6))
            .with_owner(config.ADMIN_WALLET)
            .fee_limit(10_000_000)
            .build()
            .sign(self.private_key)
        )
        return txn.broadcast()
