from .base import ExchangeWrapper
import ccxt.pro as ccxt

async def build_exchange(name, cred_block):
    """Builds an exchange wrapper asynchronously."""
    apiKey = cred_block.get('apiKey')
    secret = cred_block.get('secret')
    password = cred_block.get('password')
    return ExchangeWrapper(name, api_key=apiKey, secret=secret, password=password)
