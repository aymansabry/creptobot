import ccxt
from database.models import get_user_exchanges, log_arbitrage, update_user_balance
from services.profit_calculator import calculate_profit
from config import BOT_SHARE_PERCENT

async def start_arbitrage(user_id):
    exchanges = get_user_exchanges(user_id)
    if not exchanges:
        return {"success": False, "error": "لا توجد منصات مفعلة"}

    # مثال: مراجحة ثلاثية بين BTC/ETH/USDT
    try:
        prices = {}
        for ex in exchanges:
            client = ccxt.__getattr__(ex["name"])({
                'apiKey': ex["api_key"],
                'secret': ex["secret"],
                'password': ex.get("passphrase", "")
            })
            prices[ex["name"]] = {
                "BTCETH": client.fetch_ticker("BTC/ETH")["ask"],
                "ETHUSDT": client.fetch_ticker("ETH/USDT")["ask"],
                "BTCUSDT": client.fetch_ticker("BTC/USDT")["bid"]
            }

        # حساب الفروقات
        for name, p in prices.items():
            path = f"{name}: BTC→ETH→USDT→BTC"
            start = 1  # 1 BTC
            eth = start / p["BTCETH"]
            usdt = eth * p["ETHUSDT"]
            final_btc = usdt / p["BTCUSDT"]
            profit = final_btc - start

            if profit > 0:
                net_profit = profit * (1 - BOT_SHARE_PERCENT / 100)
                update_user_balance(user_id, net_profit)
                log_arbitrage(user_id, path, profit)
                return {"success": True, "profit": net_profit, "path": path}

        return {"success": False, "error": "لا توجد فرص مراجحة حالياً"}

    except Exception as e:
        return {"success": False, "error": str(e)}

async def stop_arbitrage(user_id):
    # مجرد علامة توقف في قاعدة البيانات
    from database.models import disable_user_trading
    disable_user_trading(user_id)
    return {"success": True}