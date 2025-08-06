import unittest
from binance.central_wallet import CentralWallet

class TestBinanceIntegration(unittest.TestCase):
    def test_balance_fetch(self):
        wallet = CentralWallet()
        balance = wallet.get_balance('USDT')
        self.assertIsInstance(balance, float)
