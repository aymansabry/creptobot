from binance import AsyncClient, BinanceSocketManager
import asyncio

class BinanceAPI:
    def __init__(self, api_key: str, api_secret: str):
        self.client = AsyncClient(api_key, api_secret)
        self.socket = BinanceSocketManager(self.client)
    
    async def get_real_time_data(self, symbol: str):
        async with self.socket.trade_socket(symbol) as ts:
            while True:
                data = await ts.recv()
                yield data
    
    async def execute_order(self, order_data: dict):
        try:
            order = await self.client.create_order(**order_data)
            return order
        except Exception as e:
            await self.client.close_connection()
            raise e
