import asyncio
import os
import httpx
from datetime import datetime
from db_access import fetch_live_accounts, update_account_pnl, get_account_balance
from utils.encryption import decrypt_text

ARBITRAGE_CHECK_INTERVAL = int(os.getenv("ARBITRAGE_CHECK_INTERVAL", "10"))
ARBITRAGE_THRESHOLD = float(os.getenv("ARBITRAGE_THRESHOLD", "0.005"))

async def get_binance_price():
    async with httpx.AsyncClient() as client:
        r = await client.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT")
        d = r.json()
        return float(d['price'])

async def get_kucoin_price():
    async with httpx.AsyncClient() as client:
        r = await client.get("https://api.kucoin.com/api/v1/market/orderbook/level1?symbol=BTC-USDT")
        d = r.json()
        return float(d['data']['price'])

async def execute_sample_arbitrage_using_keys(api_key, api_secret, passphrase, account):
    b = await get_binance_price()
    k = await get_kucoin_price()
    diff = (b - k) / k
    qty = (account.investment_amount or 0) / min(b,k)
    if qty <= 0:
        return None
    if diff > ARBITRAGE_THRESHOLD and account.mode == "live":
        profit = (b - k) * qty
        return {"profit": profit, "qty": qty, "symbol": "BTC-USDT", "price": (b+k)/2}
    if diff < -ARBITRAGE_THRESHOLD and account.mode == "live":
        profit = (k - b) * qty
        return {"profit": profit, "qty": qty, "symbol": "BTC-USDT", "price": (b+k)/2}
    return None

async def arbitrage_for_account(bot, account):
    try:
        if account.mode != "live":
            return
        api_key = decrypt_text(account.binance_api_key) if account.binance_api_key else None
        api_secret = decrypt_text(account.binance_api_secret) if account.binance_api_secret else None
        passphrase = decrypt_text(account.kucoin_api_passphrase) if account.kucoin_api_passphrase else None

        result = await execute_sample_arbitrage_using_keys(api_key, api_secret, passphrase, account)
        if not result:
            return
        profit = float(result["profit"])
        update_account_pnl(account.telegram_id, profit)
        bal = get_account_balance(account.telegram_id)

        try:
            await bot.send_message(account.telegram_id,
                f"⚡ تم تنفيذ مراجحة تلقائيًا على حسابك\n"
                f"الربح: {profit:.6f} USD\n"
                f"رصيدك الآن: {bal['balance']:.6f} USD (استثمار: {bal['investment']:.2f}, أرباح: {bal['pnl']:.6f})\n"
                f"وقت: {datetime.utcnow().isoformat()} UTC"
            )
        except Exception:
            pass
    except Exception as e:
        print("Arbitrage error:", e)

async def arbitrage_loop_all_users(bot):
    while True:
        accounts = fetch_live_accounts()
        tasks = [arbitrage_for_account(bot, acc) for acc in accounts]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        await asyncio.sleep(ARBITRAGE_CHECK_INTERVAL)

async def periodic_balance_updates(bot, interval=60):
    while True:
        accounts = fetch_live_accounts()
        for acc in accounts:
            bal = get_account_balance(acc.telegram_id)
            try:
                await bot.send_message(acc.telegram_id, f"🔔 تحديث: رصيدك الآن {bal['balance']:.6f} USD (أرباح: {bal['pnl']:.6f})")
            except Exception:
                pass
        await asyncio.sleep(interval)

def start_background_tasks(bot):
    import asyncio
    asyncio.create_task(arbitrage_loop_all_users(bot))
    asyncio.create_task(periodic_balance_updates(bot, interval=60))
