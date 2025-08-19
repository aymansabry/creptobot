import ccxt
from database.models import save_exchange_data, update_exchange_status

async def verify_exchange_connection(user_id, exchange_name, api_key, secret, passphrase=None):
    try:
        if exchange_name.lower() == "binance":
            exchange = ccxt.binance({
                'apiKey': api_key,
                'secret': secret
            })
        elif exchange_name.lower() == "coinbasepro":
            exchange = ccxt.coinbasepro({
                'apiKey': api_key,
                'secret': secret,
                'password': passphrase
            })
        else:
            return {"success": False, "error": "منصة غير مدعومة"}

        balance = exchange.fetch_balance()
        save_exchange_data(user_id, exchange_name, api_key, secret, passphrase)
        update_exchange_status(user_id, exchange_name, active=True)
        return {"success": True, "balance": balance}
    
    except Exception as e:
        update_exchange_status(user_id, exchange_name, active=False)
        return {"success": False, "error": str(e)}