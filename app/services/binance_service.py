import os
from binance.client import Client

BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")

binance_client: Client = None

async def initialize_binance_client():
    global binance_client
    if not BINANCE_API_KEY or not BINANCE_API_SECRET:
        raise ValueError("يرجى ضبط متغيرات البيئة BINANCE_API_KEY و BINANCE_API_SECRET")
    binance_client = Client(api_key=BINANCE_API_KEY, api_secret=BINANCE_API_SECRET)
