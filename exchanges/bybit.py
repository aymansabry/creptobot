from pybit.unified_trading import HTTP  # التحديث لاستخدام الواجهة الموحدة

class BybitAPI:
    def __init__(self):
        self.session = HTTP(
            api_key=config.BYBIT_API_KEY,
            api_secret=config.BYBIT_API_SECRET,
            testnet=False  # وضع التداول الحقيقي
        )
    
    async def get_orderbook(self, symbol: str):
        return self.session.get_orderbook(category="spot", symbol=symbol)  # تحديث المعلمات
