from tronpy import Tron
from tronpy.providers import HTTPProvider

class TronNetwork:
    def __init__(self, private_key: str, network: str = 'mainnet'):
        self.client = Tron(HTTPProvider(endpoint_uri=f'https://api.trongrid.io/{network}'))
        self.priv_key = private_key
    
    async def send_usdt(self, to_address: str, amount: float):
        contract = self.client.get_contract('TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t')
        txn = (
            contract.functions.transfer(to_address, int(amount * 1_000_000))
            .with_owner("OWNER_ADDRESS")
            .fee_limit(10_000_000)
            .build()
            .sign(self.priv_key)
        )
        return txn.broadcast()
