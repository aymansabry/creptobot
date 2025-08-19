from database.models import get_user_wallets
import ccxt

async def check_wallet_balance(user_id):
    wallets = get_user_wallets(user_id)
    results = []

    for wallet in wallets:
        try:
            if wallet["exchange"] == "binance":
                exchange = ccxt.binance({
                    'apiKey': wallet["api_key"],
                    'secret': wallet["secret"]
                })
            elif wallet["exchange"] == "coinbasepro":
                exchange = ccxt.coinbasepro({
                    'apiKey': wallet["api_key"],
                    'secret': wallet["secret"],
                    'password': wallet.get("passphrase", "")
                })
            else:
                results.append({"exchange": wallet["exchange"], "error": "منصة غير مدعومة"})
                continue

            balance = exchange.fetch_balance()
            total = balance['total']
            results.append({"exchange": wallet["exchange"], "balance": total})
        
        except Exception as e:
            results.append({"exchange": wallet["exchange"], "error": str(e)})
    
    return results

async def validate_investment_amount(user_id, amount):
    balances = await check_wallet_balance(user_id)
    total_available = 0

    for b in balances:
        if "balance" in b:
            total_available += sum(b["balance"].values())

    if total_available >= amount:
        return {"success": True, "available": total_available}
    else:
        return {"success": False, "available": total_available}