# utils/tron_utils.py

import aiohttp
from config.config import Config

TRON_API_URL = "https://api.trongrid.io"

async def get_tron_balance(address):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{TRON_API_URL}/v1/accounts/{address}") as resp:
            data = await resp.json()
            try:
                return int(data["data"][0]["balance"]) / 1_000_000  # TRX has 6 decimals
            except:
                return 0

async def send_tron_transaction(from_address, to_address, amount, private_key):
    # Placeholder: implement real Tron transaction if required using tronpy or tronapi
    pass
