from .auth import register_handlers as register_auth
from .trading import register_handlers as register_trading
from .wallet import register_handlers as register_wallet

def register_handlers(dp):
    register_auth(dp)
    register_trading(dp)
    register_wallet(dp)
