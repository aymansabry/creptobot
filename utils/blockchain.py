import httpx
from config import settings

# مثال لـ TRON API
async def check_wallet_received(address: str, expected_amount: float) -> bool:
    async with httpx.AsyncClient() as client:
        url = f"https://api.trongrid.io/v1/accounts/{address}/transactions/trc20"
        headers = {"TRON-PRO-API-KEY": settings.TRONGRID_API_KEY}
        resp = await client.get(url, headers=headers)
        data = resp.json()
        for tx in data.get("data", []):
            if tx["to"] == address and float(tx["value"]) / 1e6 >= expected_amount:
                return True
    return False

async def transfer_usdt(to_address: str, amount: float) -> bool:
    # في النسخة الحالية: وهمي فقط - للطباعة
    print(f"Transferring {amount} USDT to {to_address}")
    return True
